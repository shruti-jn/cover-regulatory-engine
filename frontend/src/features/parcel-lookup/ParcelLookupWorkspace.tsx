import { Suspense, lazy } from "react";

import { DemoParcel } from "../../data/demoStudio";
import "./parcel-lookup.css";

const ParcelMap = lazy(async () => {
  const module = await import("../../components/map/ParcelMap");
  return { default: module.ParcelMap };
});

type ParcelLookupWorkspaceProps = {
  parcels: DemoParcel[];
  selectedParcelId: string;
  onSelectParcel: (parcelId: string) => void;
};

export function ParcelLookupWorkspace({ parcels, selectedParcelId, onSelectParcel }: ParcelLookupWorkspaceProps) {
  const selectedParcel = parcels.find((parcel) => parcel.id === selectedParcelId) ?? parcels[0];
  const comparisonRows = parcels.map((parcel) => ({
    id: parcel.id,
    label: parcel.label,
    zone: parcel.zone,
    confidence: Math.round(parcel.confidence * 100),
    unresolvedItems: parcel.unresolvedItems,
    tag: parcel.comparisonTag,
  }));

  return (
    <section className="parcel-lookup-workspace" id="parcel-lookup-workspace">
      <div className="lookup-controls" id="lookup-controls">
        <div className="lookup-header-copy">
          <p className="eyebrow">Parcel library</p>
          <h2>Map-first parcel review</h2>
          <p>Switch parcels and keep geometry, rules, and recommendation connected.</p>
        </div>
        <div className="parcel-selector" role="tablist" aria-label="Demo parcels">
          {parcels.map((parcel) => (
            <button
              key={parcel.id}
              type="button"
              role="tab"
              aria-selected={parcel.id === selectedParcelId}
              className={`parcel-chip ${parcel.id === selectedParcelId ? "parcel-chip-active" : ""}`}
              onClick={() => onSelectParcel(parcel.id)}
            >
              <strong>{parcel.label}</strong>
              <span>{parcel.zone}{parcel.overlays.length > 0 ? ` + ${parcel.overlays.join(" + ")}` : ""}</span>
            </button>
          ))}
        </div>
      </div>

      <section className="parcel-map-panel" id="parcel-map">
        <div className="map-stage-header">
          <div>
            <p className="eyebrow">Parcel canvas</p>
            <h3>{selectedParcel.address}</h3>
          </div>
          <div className="map-stage-metadata">
            <div className="accuracy-cluster" data-testid="accuracy-flag">
              <span className="eyebrow">Geocode confidence</span>
              <strong className={`accuracy-pill accuracy-${selectedParcel.geocodeConfidence.toLowerCase()}`}>
                {selectedParcel.geocodeConfidence}
              </strong>
            </div>
            <div className="map-stage-note">
              <span className="eyebrow">Source snapshot</span>
              <strong>{selectedParcel.sourceSnapshot}</strong>
            </div>
          </div>
        </div>
        <Suspense fallback={<div className="parcel-map-frame loading-map">Loading map workspace...</div>}>
          <ParcelMap geometry={selectedParcel.geometry} accuracyFlag={selectedParcel.geocodeConfidence} />
        </Suspense>
        <div className="map-overlay-strip">
          <div>
            <span className="overlay-label">Zoning frame</span>
            <strong>{selectedParcel.zone}{selectedParcel.overlays.length > 0 ? ` + ${selectedParcel.overlays.join(" + ")}` : ""}</strong>
          </div>
          <div>
            <span className="overlay-label">Lot size</span>
            <strong>{selectedParcel.lotSize}</strong>
          </div>
          <div>
            <span className="overlay-label">Review focus</span>
            <strong>{selectedParcel.reviewFocus}</strong>
          </div>
        </div>
        <div className="map-confirmation-card">
          <div>
            <span className="eyebrow">Parcel confirmation</span>
            <h3>{selectedParcel.neighborhood}</h3>
            <p>Boundary, inset envelope, and review posture are visible immediately so the first screen behaves like a working instrument instead of a pretty placeholder.</p>
          </div>
          <div className="confirmation-facts">
            <div>
              <span>APN</span>
              <strong>{selectedParcel.apn}</strong>
            </div>
            <div>
              <span>Frontage</span>
              <strong>{selectedParcel.frontage}</strong>
            </div>
          </div>
        </div>
      </section>

      <aside className="parcel-facts-panel" id="parcel-facts">
        <div className="panel-card">
          <div className="panel-heading">
            <p className="eyebrow">Portfolio compare</p>
            <span className="source-timestamp">Batch-ready</span>
          </div>
          <div className="comparison-table" role="table" aria-label="Parcel comparison table">
            <div className="comparison-table-header" role="row">
              <span>Parcel</span>
              <span>Zone</span>
              <span>Confidence</span>
              <span>Open items</span>
            </div>
            {comparisonRows.map((row) => (
              <button
                key={row.id}
                type="button"
                className={`comparison-row ${row.id === selectedParcelId ? "comparison-row-active" : ""}`}
                onClick={() => onSelectParcel(row.id)}
              >
                <div>
                  <strong>{row.label}</strong>
                  <span>{row.tag}</span>
                </div>
                <span>{row.zone}</span>
                <span>{row.confidence}%</span>
                <span>{row.unresolvedItems}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="panel-card site-sheet-card">
          <div className="panel-heading">
            <p className="eyebrow">Commercial readout</p>
            <span className="source-timestamp">Sales-ready</span>
          </div>
          <div className="site-sheet-grid">
            <div>
              <span>Parcel type</span>
              <strong>{selectedParcel.comparisonTag}</strong>
            </div>
            <div>
              <span>Next step</span>
              <strong>{selectedParcel.nextStep}</strong>
            </div>
            <div>
              <span>Sales framing</span>
              <strong>{selectedParcel.salesNarrative}</strong>
            </div>
            <div>
              <span>Homeowner framing</span>
              <strong>{selectedParcel.homeownerNarrative}</strong>
            </div>
          </div>
        </div>
      </aside>
    </section>
  );
}
