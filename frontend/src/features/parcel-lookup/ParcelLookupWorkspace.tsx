import { FormEvent, Suspense, lazy, useState } from "react";
import "./parcel-lookup.css";

const ParcelMap = lazy(async () => {
  const module = await import("../../components/map/ParcelMap");
  return { default: module.ParcelMap };
});

type GeocodeCandidate = {
  apn: string;
  formatted_address: string;
  place_id: string;
  accuracy_flag: "ROOFTOP" | "INTERPOLATED";
};

type ParcelResponse = {
  apn: string;
  address: string;
  geometry: {
    type: "Polygon";
    coordinates: number[][][];
  };
  geocoding_metadata?: {
    accuracy_flag?: string | null;
  } | null;
};

type WorkspaceState =
  | { mode: "idle" }
  | { mode: "loading" }
  | { mode: "ready"; candidate: GeocodeCandidate; parcel: ParcelResponse }
  | { mode: "error"; message: string };

const SAMPLE_CANDIDATE: GeocodeCandidate = {
  apn: "5419-023-018",
  formatted_address: "1321 Lucile Ave, Los Angeles, CA 90026",
  place_id: "sample-place-id",
  accuracy_flag: "ROOFTOP",
};

const SAMPLE_PARCEL: ParcelResponse = {
  apn: "5419-023-018",
  address: "1321 Lucile Ave, Los Angeles, CA 90026",
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [-118.2591, 34.0897],
        [-118.2584, 34.0897],
        [-118.2584, 34.0892],
        [-118.2591, 34.0892],
        [-118.2591, 34.0897],
      ],
    ],
  },
  geocoding_metadata: {
    accuracy_flag: "ROOFTOP",
  },
};

export function ParcelLookupWorkspace() {
  const [query, setQuery] = useState("1321 Lucile Ave, Los Angeles, CA");
  const [workspaceState, setWorkspaceState] = useState<WorkspaceState>({
    mode: "ready",
    candidate: SAMPLE_CANDIDATE,
    parcel: SAMPLE_PARCEL,
  });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setWorkspaceState({ mode: "error", message: "Enter an address or APN to review a parcel." });
      return;
    }

    setWorkspaceState({ mode: "loading" });

    try {
      const geocodeResponse = await fetch(`/api/v1/parcels/geocode?address=${encodeURIComponent(trimmed)}`);
      if (!geocodeResponse.ok) {
        throw new Error("Geocoding lookup failed");
      }

      const geocodePayload = (await geocodeResponse.json()) as { candidates: GeocodeCandidate[] };
      const candidate = geocodePayload.candidates[0];
      if (!candidate) {
        throw new Error("No parcel candidates returned");
      }

      const parcelResponse = await fetch(`/api/v1/parcels/${candidate.apn}`);
      if (!parcelResponse.ok) {
        throw new Error("Parcel facts could not be loaded");
      }

      const parcel = (await parcelResponse.json()) as ParcelResponse;
      setWorkspaceState({ mode: "ready", candidate, parcel });
    } catch {
      setWorkspaceState({
        mode: "error",
        message:
          "Live parcel services are unavailable right now. The workspace is preserved so you can retry or review the sample parcel shell.",
      });
    }
  }

  const candidate = workspaceState.mode === "ready" ? workspaceState.candidate : SAMPLE_CANDIDATE;
  const parcel = workspaceState.mode === "ready" ? workspaceState.parcel : SAMPLE_PARCEL;

  return (
    <section className="parcel-lookup-workspace" id="parcel-lookup-workspace">
      <header className="lookup-controls" id="lookup-controls">
        <form className="lookup-form" onSubmit={handleSubmit}>
          <label className="search-field search-field-parcel">
            <span className="search-label">Address or APN</span>
            <input
              aria-label="Address or APN"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Enter parcel address or APN"
            />
          </label>
          <button className="primary-action" type="submit" disabled={workspaceState.mode === "loading"}>
            {workspaceState.mode === "loading" ? "Loading parcel" : "Locate parcel"}
          </button>
        </form>

        <div className="lookup-meta">
          <div className="accuracy-cluster" data-testid="accuracy-flag">
            <span className="eyebrow">Geocode confidence</span>
            <strong className={`accuracy-pill accuracy-${candidate.accuracy_flag.toLowerCase()}`}>
              {candidate.accuracy_flag}
            </strong>
          </div>
          <div className="lookup-hint">
            {workspaceState.mode === "error" ? (
              <p className="recoverable-message">{workspaceState.message}</p>
            ) : (
              <p>Map geometry, parcel facts, and confidence stay visible while you iterate on parcel lookup.</p>
            )}
          </div>
        </div>
      </header>

      <section className="parcel-map-panel" id="parcel-map">
        <Suspense fallback={<div className="parcel-map-frame loading-map">Loading map workspace...</div>}>
          <ParcelMap geometry={parcel.geometry} accuracyFlag={candidate.accuracy_flag} />
        </Suspense>
        <div className="map-confirmation-card">
          <span className="eyebrow">Parcel confirmation</span>
          <h3>{candidate.formatted_address}</h3>
          <p>Boundary and setback inset are shown directly on the map so architects can visually confirm parcel placement before deeper review.</p>
        </div>
      </section>

      <aside className="parcel-facts-panel" id="parcel-facts">
        <div className="panel-card">
          <div className="panel-heading">
            <p className="eyebrow">Parcel facts</p>
            <span className="source-timestamp">Source snapshot Mar 22</span>
          </div>
          <dl className="fact-list">
            <div>
              <dt>APN</dt>
              <dd>{parcel.apn}</dd>
            </div>
            <div>
              <dt>Address</dt>
              <dd>{parcel.address}</dd>
            </div>
            <div>
              <dt>Lookup mode</dt>
              <dd>{candidate.accuracy_flag === "ROOFTOP" ? "Precise rooftop match" : "Interpolated frontage match"}</dd>
            </div>
            <div>
              <dt>Place ID</dt>
              <dd>{candidate.place_id}</dd>
            </div>
          </dl>
        </div>
      </aside>
    </section>
  );
}
