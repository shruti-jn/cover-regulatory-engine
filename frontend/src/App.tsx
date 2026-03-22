import { useState } from "react";

import { demoParcels, studioMarkers } from "./data/demoStudio";
import { AssessmentWorkspace } from "./features/assessment/AssessmentWorkspace";
import { ParcelLookupWorkspace } from "./features/parcel-lookup/ParcelLookupWorkspace";

export default function App() {
  const [selectedParcelId, setSelectedParcelId] = useState(demoParcels[0].id);
  const [audienceMode, setAudienceMode] = useState<"architect" | "sales">("architect");
  const selectedParcel = demoParcels.find((parcel) => parcel.id === selectedParcelId) ?? demoParcels[0];

  return (
    <div className="app-shell">
      <header className="studio-header">
        <div className="studio-header-copy">
          <p className="eyebrow">Cover regulatory engine</p>
          <h1>Buildability workstation</h1>
          <p>
            A parcel-native review surface for architects and sales teams to understand feasibility, explain risk, and hand off a deterministic client story.
          </p>
        </div>
        <div className="studio-header-controls">
          <div className="studio-banner-markers">
            {studioMarkers.map((marker) => (
              <span key={marker} className="context-chip studio-chip">
                {marker}
              </span>
            ))}
          </div>
          <div className="audience-toggle" role="tablist" aria-label="Audience mode">
            {(["architect", "sales"] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                role="tab"
                aria-selected={audienceMode === mode}
                className={audienceMode === mode ? "audience-toggle-active" : ""}
                onClick={() => setAudienceMode(mode)}
              >
                {mode === "architect" ? "Architect mode" : "Sales mode"}
              </button>
            ))}
          </div>
        </div>
      </header>

      <section className="mission-strip" aria-label="How Cover works">
        <div className="mission-card">
          <span className="eyebrow">1. Resolve parcel</span>
          <strong>{selectedParcel.address}</strong>
        </div>
        <div className="mission-card">
          <span className="eyebrow">2. Apply rules</span>
          <strong>{selectedParcel.zone}{selectedParcel.overlays.length > 0 ? ` + ${selectedParcel.overlays.join(" + ")}` : ""}</strong>
        </div>
        <div className="mission-card">
          <span className="eyebrow">3. Explain recommendation</span>
          <strong>{selectedParcel.verdictTitle}</strong>
        </div>
      </section>

      <main className="workspace-grid" id="workspace-shell">
        <ParcelLookupWorkspace
          parcels={demoParcels}
          selectedParcelId={selectedParcelId}
          onSelectParcel={setSelectedParcelId}
        />

        <AssessmentWorkspace parcel={selectedParcel} audienceMode={audienceMode} />
      </main>
    </div>
  );
}
