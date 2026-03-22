import { ParcelLookupWorkspace } from "./features/parcel-lookup/ParcelLookupWorkspace";

const evidenceItems = [
  {
    title: "Front setback controls envelope depth",
    state: "deterministic",
    note: "LAMC frontage rule applied with parcel geometry",
  },
  {
    title: "Hillside interpretation still open",
    state: "interpreted",
    note: "Escalate for manual confirmation before client export",
  },
  {
    title: "Driveway width still unresolved",
    state: "unresolved",
    note: "Await parcel-specific frontage verification",
  },
];

const searchPills = ["90026", "RS-1", "ADU", "HPOZ"];

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar" id="search-bar">
        <div>
          <p className="eyebrow">Cover regulatory engine</p>
          <h1>Project buildability workstation</h1>
        </div>
        <div className="search-area">
          <label className="search-field">
            <span className="search-label">Address or APN</span>
            <input defaultValue="1321 Lucile Ave, Los Angeles, CA" aria-label="Address or APN" />
          </label>
          <button className="primary-action" type="button">
            Review parcel
          </button>
        </div>
      </header>

      <main className="workspace-grid" id="workspace-shell">
        <section className="summary-rail" id="hero-summary">
          <div className="summary-card verdict-card">
            <div>
              <p className="eyebrow">Quick verdict</p>
              <h2>Likely ADU-ready with hillside caution</h2>
            </div>
            <div className="metric-row">
              <div>
                <span className="metric-value">0.84</span>
                <span className="metric-label">confidence</span>
              </div>
              <div>
                <span className="metric-value">3</span>
                <span className="metric-label">active constraints</span>
              </div>
              <div>
                <span className="metric-value">1</span>
                <span className="metric-label">needs review</span>
              </div>
            </div>
          </div>

          <div className="summary-card chip-card">
            <p className="eyebrow">Recent context</p>
            <div className="chip-row">
              {searchPills.map((pill) => (
                <span key={pill} className="context-chip">
                  {pill}
                </span>
              ))}
            </div>
          </div>
        </section>

        <ParcelLookupWorkspace />

        <aside className="evidence-panel" id="evidence-panel">
          <section className="panel-card">
            <div className="panel-heading">
              <p className="eyebrow">Evidence and citations</p>
              <span className="source-timestamp">Updated Mar 22</span>
            </div>
            <div className="evidence-list">
              {evidenceItems.map((item) => (
                <article key={item.title} className="evidence-item">
                  <div className="evidence-header">
                    <h3>{item.title}</h3>
                    <span className={`state-pill state-${item.state}`}>{item.state}</span>
                  </div>
                  <p>{item.note}</p>
                </article>
              ))}
            </div>
          </section>
        </aside>
      </main>
    </div>
  );
}
