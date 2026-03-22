import "./constraints.css";

type ProvenanceBadgeProps = {
  state: "deterministic" | "interpreted" | "unresolved";
};

export function ProvenanceBadge({ state }: ProvenanceBadgeProps) {
  return (
    <span className={`provenance-badge provenance-${state}`}>
      <span className="provenance-dot" aria-hidden="true" />
      {state}
    </span>
  );
}
