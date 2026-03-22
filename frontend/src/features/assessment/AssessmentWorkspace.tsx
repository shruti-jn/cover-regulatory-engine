import { useMemo, useState } from "react";

import { ConstraintCard, ConstraintCardModel } from "../../components/constraints/ConstraintCard";
import { ProvenanceBadge } from "../../components/constraints/ProvenanceBadge";
import "./assessment.css";

type ViewMode = "2D" | "3D";

type ScenarioOption = {
  id: string;
  label: string;
  buildingType: string;
  bedrooms: number;
};

const scenarioOptions: ScenarioOption[] = [
  { id: "adu-1", label: "ADU / 1 bed", buildingType: "ADU", bedrooms: 1 },
  { id: "adu-3", label: "ADU / 3 bed", buildingType: "ADU", bedrooms: 3 },
  { id: "sfh-4", label: "SFH / 4 bed", buildingType: "SFH", bedrooms: 4 },
];

const scenarioConstraints: Record<string, ConstraintCardModel[]> = {
  "adu-1": [
    {
      domain: "setback",
      provenanceState: "deterministic",
      confidenceScore: 0.92,
      valueLabel: "16 ft setback envelope",
      citationLabel: "LAMC 12.21",
      evidenceExcerpt: "Front yard rule applied to the current parcel frontage geometry.",
    },
    {
      domain: "parking",
      provenanceState: "interpreted",
      confidenceScore: 0.74,
      valueLabel: "1 stall likely required",
      citationLabel: "LAMC parking note",
      evidenceExcerpt: "Parking relief depends on transit assumptions and needs project confirmation.",
    },
    {
      domain: "hillside",
      provenanceState: "unresolved",
      confidenceScore: 0.43,
      valueLabel: "Manual hillside check",
      citationLabel: "Hillside overlay review",
      evidenceExcerpt: "Topographic interpretation still needs expert review before final signoff.",
    },
  ],
  "adu-3": [
    {
      domain: "setback",
      provenanceState: "deterministic",
      confidenceScore: 0.92,
      valueLabel: "16 ft setback envelope",
      citationLabel: "LAMC 12.21",
      evidenceExcerpt: "Front yard rule applied to the current parcel frontage geometry.",
    },
    {
      domain: "parking",
      provenanceState: "interpreted",
      confidenceScore: 0.7,
      valueLabel: "2 stalls likely required",
      citationLabel: "LAMC parking note",
      evidenceExcerpt: "Bedroom increase changes likely parking demand and affects planning narrative.",
    },
    {
      domain: "height",
      provenanceState: "deterministic",
      confidenceScore: 0.88,
      valueLabel: "24 ft massing cap",
      citationLabel: "Height envelope",
      evidenceExcerpt: "Height limit stays stable but changes the visible 3D envelope profile.",
    },
  ],
  "sfh-4": [
    {
      domain: "setback",
      provenanceState: "deterministic",
      confidenceScore: 0.92,
      valueLabel: "18 ft setback envelope",
      citationLabel: "LAMC 12.21",
      evidenceExcerpt: "Setback expands slightly with the single-family scenario assumptions.",
    },
    {
      domain: "parking",
      provenanceState: "deterministic",
      confidenceScore: 0.84,
      valueLabel: "2 covered stalls",
      citationLabel: "Parking requirement",
      evidenceExcerpt: "Parking requirement becomes clearer for the single-family configuration.",
    },
    {
      domain: "hillside",
      provenanceState: "interpreted",
      confidenceScore: 0.62,
      valueLabel: "Slope adjustment possible",
      citationLabel: "Hillside guidance",
      evidenceExcerpt: "Interpretive hillside logic still needs final review before export.",
    },
  ],
};

export function AssessmentWorkspace() {
  const [viewMode, setViewMode] = useState<ViewMode>("2D");
  const [selectedScenarioId, setSelectedScenarioId] = useState("adu-1");
  const baselineScenario = scenarioOptions[0];
  const selectedScenario = scenarioOptions.find((scenario) => scenario.id === selectedScenarioId) ?? baselineScenario;
  const constraints = scenarioConstraints[selectedScenario.id];

  const changedConstraints = useMemo(() => {
    const baselineByDomain = new Map(scenarioConstraints[baselineScenario.id].map((constraint) => [constraint.domain, constraint]));
    return constraints
      .filter((constraint) => {
        const baseline = baselineByDomain.get(constraint.domain);
        return !baseline || baseline.valueLabel !== constraint.valueLabel || baseline.provenanceState !== constraint.provenanceState;
      })
      .map((constraint) => ({
        domain: constraint.domain,
        afterValue: constraint.valueLabel,
      }));
  }, [constraints, baselineScenario.id]);

  return (
    <aside className="assessment-workspace" id="assessment-workspace">
      <section className="panel-card assessment-summary" id="assessment-summary">
        <div className="assessment-summary-header">
          <div>
            <p className="eyebrow">Assessment summary</p>
            <h2>Architect review packet</h2>
          </div>
          <ProvenanceBadge state="deterministic" />
        </div>
        <div className="assessment-metrics">
          <div>
            <span className="metric-value">3</span>
            <span className="metric-label">active constraints</span>
          </div>
          <div>
            <span className="metric-value">1</span>
            <span className="metric-label">unresolved item</span>
          </div>
          <div>
            <span className="metric-value">{selectedScenario.buildingType}</span>
            <span className="metric-label">scenario</span>
          </div>
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
          <div className="visual-parcel-shell">
            <div className="visual-envelope" />
            {viewMode === "3D" ? <div className="visual-volume" /> : null}
          </div>
          <div className="visual-stage-caption">
            {viewMode === "2D"
              ? "Plan view shows parcel shell, setback-derived envelope, and citation-linked overlay state."
              : "3D view shows massing volume constrained by the active setback and height assumptions."}
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
          {scenarioOptions.map((scenario) => (
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
            <p className="scenario-diff-empty">No changed constraints relative to the baseline ADU study.</p>
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
    </aside>
  );
}
