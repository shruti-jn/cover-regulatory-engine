import { useEffect, useMemo, useState } from "react";

import { ConstraintCard, ConstraintCardModel } from "../../components/constraints/ConstraintCard";
import { ProvenanceBadge } from "../../components/constraints/ProvenanceBadge";
import { DemoParcel } from "../../data/demoStudio";
import "./assessment.css";

type ViewMode = "2D" | "3D";
type AudienceMode = "architect" | "sales";

type AssessmentWorkspaceProps = {
  parcel: DemoParcel;
  audienceMode: AudienceMode;
};

export function AssessmentWorkspace({ parcel, audienceMode }: AssessmentWorkspaceProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("2D");
  const [selectedScenarioId, setSelectedScenarioId] = useState(parcel.scenarios[0]?.id ?? "");

  useEffect(() => {
    setSelectedScenarioId(parcel.scenarios[0]?.id ?? "");
  }, [parcel.id, parcel.scenarios]);

  const baselineScenario = parcel.scenarios[0];
  const selectedScenario = parcel.scenarios.find((scenario) => scenario.id === selectedScenarioId) ?? baselineScenario;
  const constraints: ConstraintCardModel[] = selectedScenario?.constraints ?? [];

  const changedConstraints = useMemo(() => {
    if (!baselineScenario || !selectedScenario) {
      return [];
    }

    const baselineByDomain = new Map(baselineScenario.constraints.map((constraint) => [constraint.domain, constraint]));
    return constraints
      .filter((constraint) => {
        const baseline = baselineByDomain.get(constraint.domain);
        return !baseline || baseline.valueLabel !== constraint.valueLabel || baseline.provenanceState !== constraint.provenanceState;
      })
      .map((constraint) => ({
        domain: constraint.domain,
        afterValue: constraint.valueLabel,
      }));
  }, [constraints, baselineScenario, selectedScenario]);

  if (!baselineScenario || !selectedScenario) {
    return null;
  }

  return (
    <aside className="assessment-workspace" id="assessment-workspace">
      <section className="panel-card assessment-summary" id="assessment-summary">
        <div className="assessment-summary-header">
          <div>
            <p className="eyebrow">Assessment summary</p>
            <h2>{audienceMode === "architect" ? "Architect review packet" : "Client-ready parcel brief"}</h2>
            <p className="assessment-summary-copy">
              {audienceMode === "architect"
                ? "Constraint decisions stay visible with citations, provenance state, and scenario-sensitive geometry cues."
                : "Sales and homeowner conversations stay evidence-linked, calm, and deterministic instead of hand-wavy."}
            </p>
          </div>
          <ProvenanceBadge state="deterministic" />
        </div>
        <div className="assessment-metrics">
          <div>
            <span className="metric-value">{parcel.activeConstraints}</span>
            <span className="metric-label">active constraints</span>
          </div>
          <div>
            <span className="metric-value">{parcel.unresolvedItems}</span>
            <span className="metric-label">unresolved item</span>
          </div>
          <div>
            <span className="metric-value">{selectedScenario.buildingType}</span>
            <span className="metric-label">scenario</span>
          </div>
        </div>
        <div className="evidence-ribbon">
          <div>
            <span className="evidence-ribbon-label">Verdict</span>
            <strong>{parcel.verdictTitle}</strong>
          </div>
          <div>
            <span className="evidence-ribbon-label">Next move</span>
            <strong>{parcel.nextStep}</strong>
          </div>
        </div>
        <div className="packet-note">
          <span className="eyebrow">Packet note</span>
          <p>{selectedScenario.summary}</p>
        </div>
      </section>

      <section className="panel-card visualization-stage" id="visualization-stage">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Visualization stage</p>
            <h3>Constraint-aware buildable envelope</h3>
          </div>
          <div className="mode-toggle">
            {(["2D", "3D"] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                className={mode === viewMode ? "mode-toggle-active" : undefined}
                type="button"
                onClick={() => setViewMode(mode)}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
        <div className={`visual-stage-scene visual-stage-${viewMode.toLowerCase()}`}>
          <div className="visual-stage-annotation annotation-top-left">Street edge</div>
          <div className="visual-stage-annotation annotation-top-right">{parcel.zone}</div>
          <div className="visual-stage-annotation annotation-bottom-left">{parcel.overlays.length > 0 ? parcel.overlays.join(" + ") : "Base zone"}</div>
          <div className="visual-parcel-shell">
            <div className="visual-lot-shadow" />
            <div className="visual-envelope" />
            <div className="visual-setback-band" />
            {viewMode === "3D" ? <div className="visual-volume" /> : null}
          </div>
          <div className="visual-stage-stats">
            <div>
              <span>Footprint</span>
              <strong>{selectedScenario.footprintLabel}</strong>
            </div>
            <div>
              <span>Height cap</span>
              <strong>{selectedScenario.heightCap}</strong>
            </div>
            <div>
              <span>Open issue</span>
              <strong>{selectedScenario.unresolvedLabel}</strong>
            </div>
          </div>
          <div className="visual-stage-caption">
            {viewMode === "2D"
              ? "Plan view shows parcel shell, setback-derived envelope, and the exact review posture that shapes the recommendation."
              : "3D view shows a massing read that sales can explain and architects can challenge without losing the evidence chain."}
          </div>
        </div>
      </section>

      <section className="panel-card scenario-panel" id="scenario-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Scenario controls</p>
            <h3>What changed</h3>
          </div>
        </div>
        <div className="scenario-options">
          {parcel.scenarios.map((scenario) => (
            <button
              key={scenario.id}
              type="button"
              className={`scenario-option ${scenario.id === selectedScenarioId ? "scenario-option-active" : ""}`}
              onClick={() => setSelectedScenarioId(scenario.id)}
            >
              <strong>{scenario.label}</strong>
              <span>{scenario.buildingType} with {scenario.bedrooms} bedroom{scenario.bedrooms > 1 ? "s" : ""}</span>
            </button>
          ))}
        </div>
        <div className="scenario-diff-card">
          <p className="eyebrow">Scenario diff</p>
          {changedConstraints.length === 0 ? (
            <p className="scenario-diff-empty">No changed constraints relative to the baseline study.</p>
          ) : (
            <ul>
              {changedConstraints.map((constraint) => (
                <li key={constraint.domain}>
                  <strong>{constraint.domain}</strong>
                  <span>{constraint.afterValue}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="scenario-note">
          <span className="eyebrow">{audienceMode === "architect" ? "Design reading" : "Client framing"}</span>
          <p>{selectedScenario.narrative}</p>
        </div>
      </section>

      <section className="panel-card workflow-panel" id="workflow-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Approval workflow</p>
            <h3>Deterministic handoff state</h3>
          </div>
        </div>
        <div className="workflow-steps">
          <div className="workflow-step workflow-step-complete">
            <span>1</span>
            <div>
              <strong>Lookup confirmed</strong>
              <p>Parcel geometry and source snapshot are visible.</p>
            </div>
          </div>
          <div className="workflow-step workflow-step-complete">
            <span>2</span>
            <div>
              <strong>Assessment assembled</strong>
              <p>Constraints, confidence, and citations are connected.</p>
            </div>
          </div>
          <div className={`workflow-step ${parcel.unresolvedItems > 0 ? "workflow-step-open" : "workflow-step-complete"}`}>
            <span>3</span>
            <div>
              <strong>{parcel.unresolvedItems > 0 ? "Architect signoff required" : "Ready for client packet"}</strong>
              <p>{parcel.unresolvedItems > 0 ? parcel.nextStep : "No unresolved blockers remain in the current study."}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="panel-card constraint-details" id="constraint-details">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Constraint details</p>
            <h3>Citations and evidence</h3>
          </div>
        </div>
        <div className="constraint-list">
          {constraints.map((constraint) => (
            <ConstraintCard key={`${selectedScenario.id}-${constraint.domain}`} constraint={constraint} />
          ))}
        </div>
      </section>

      <section className="panel-card handoff-panel" id="handoff-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Client handoff</p>
            <h3>What Cover can say next</h3>
          </div>
        </div>
        <div className="handoff-copy">
          <p>{parcel.salesNarrative}</p>
          <p>{parcel.homeownerNarrative}</p>
        </div>
        <div className="handoff-actions">
          <button type="button" className="primary-action">Export review packet</button>
          <button type="button" className="secondary-action">Share comparison sheet</button>
        </div>
      </section>
    </aside>
  );
}
