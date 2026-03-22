import { ProvenanceBadge } from "./ProvenanceBadge";
import "./constraints.css";

export type ConstraintCardModel = {
  domain: string;
  provenanceState: "deterministic" | "interpreted" | "unresolved";
  confidenceScore: number;
  valueLabel: string;
  citationLabel: string;
  evidenceExcerpt: string;
};

type ConstraintCardProps = {
  constraint: ConstraintCardModel;
};

export function ConstraintCard({ constraint }: ConstraintCardProps) {
  return (
    <article className="constraint-card">
      <div className="constraint-card-header">
        <div>
          <p className="eyebrow">Constraint</p>
          <h3>{constraint.domain}</h3>
        </div>
        <ProvenanceBadge state={constraint.provenanceState} />
      </div>
      <p className="constraint-value">{constraint.valueLabel}</p>
      <div className="constraint-meta">
        <span>{Math.round(constraint.confidenceScore * 100)}% confidence</span>
        <button type="button" className="citation-link">
          {constraint.citationLabel}
        </button>
      </div>
      <p className="constraint-evidence">{constraint.evidenceExcerpt}</p>
    </article>
  );
}
