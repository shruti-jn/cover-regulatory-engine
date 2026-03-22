export type DemoConstraint = {
  domain: string;
  provenanceState: "deterministic" | "interpreted" | "unresolved";
  confidenceScore: number;
  valueLabel: string;
  citationLabel: string;
  evidenceExcerpt: string;
};

export type DemoScenario = {
  id: string;
  label: string;
  buildingType: string;
  bedrooms: number;
  summary: string;
  footprintLabel: string;
  heightCap: string;
  unresolvedLabel: string;
  narrative: string;
  constraints: DemoConstraint[];
};

export type DemoParcel = {
  id: string;
  label: string;
  address: string;
  apn: string;
  neighborhood: string;
  zone: string;
  overlays: string[];
  lotSize: string;
  frontage: string;
  geocodeConfidence: "ROOFTOP" | "INTERPOLATED";
  geometry: {
    type: "Polygon";
    coordinates: number[][][];
  };
  verdictTitle: string;
  verdictDetail: string;
  confidence: number;
  activeConstraints: number;
  unresolvedItems: number;
  reviewFocus: string;
  nextStep: string;
  sourceSnapshot: string;
  salesNarrative: string;
  homeownerNarrative: string;
  comparisonTag: string;
  scenarios: DemoScenario[];
};

export const studioMarkers = ["Los Angeles", "Single parcel + portfolio", "Evidence-linked", "2D + 3D"];

export const dataSources = [
  "LAMC Chapter 12 ruleset",
  "CA ADU law (AB 68 / SB 13 / AB 881)",
  "ZIMAS verification workflow",
  "LA County parcel enrichment",
];

export const demoParcels: DemoParcel[] = [
  {
    id: "parcel-a",
    label: "Parcel A",
    address: "1321 Lucile Ave, Los Angeles, CA 90026",
    apn: "5419-023-018",
    neighborhood: "Silver Lake",
    zone: "RS-1",
    overlays: [],
    lotSize: "7,080 sf",
    frontage: "Lucile Ave frontage",
    geocodeConfidence: "ROOFTOP",
    geometry: {
      type: "Polygon",
      coordinates: [[[-118.2591, 34.0897], [-118.2584, 34.0897], [-118.2584, 34.0892], [-118.2591, 34.0892], [-118.2591, 34.0897]]],
    },
    verdictTitle: "Likely ADU-ready with one hillside clarification",
    verdictDetail: "The baseline lot reads as an efficient single-parcel feasibility case: clear frontage, stable setbacks, and one open review item before client export.",
    confidence: 0.84,
    activeConstraints: 3,
    unresolvedItems: 1,
    reviewFocus: "Setback, parking, hillside",
    nextStep: "Confirm hillside reading and export client packet",
    sourceSnapshot: "Verified Mar 22",
    salesNarrative: "Strong first-call parcel. Fast path to a confident ADU conversation with only one explicit caution to explain.",
    homeownerNarrative: "This lot appears promising for an ADU concept, and the remaining caveat is transparent rather than hidden.",
    comparisonTag: "Fastest path",
    scenarios: [
      {
        id: "adu-1",
        label: "ADU / 1 bed",
        buildingType: "ADU",
        bedrooms: 1,
        summary: "Cleanest envelope for early client conversation.",
        footprintLabel: "1,180 sf",
        heightCap: "22 ft",
        unresolvedLabel: "Manual hillside review",
        narrative: "Baseline ADU study preserves the cleanest envelope and keeps the homeowner story simple.",
        constraints: [
          {
            domain: "setback",
            provenanceState: "deterministic",
            confidenceScore: 0.92,
            valueLabel: "16 ft front setback envelope",
            citationLabel: "LAMC 12.21",
            evidenceExcerpt: "Front yard rule applied to the parcel frontage geometry with no overlay adjustment.",
          },
          {
            domain: "parking",
            provenanceState: "interpreted",
            confidenceScore: 0.74,
            valueLabel: "1 stall likely required",
            citationLabel: "LAMC parking note",
            evidenceExcerpt: "Parking relief depends on transit assumptions and should be confirmed before permit filing.",
          },
          {
            domain: "hillside",
            provenanceState: "unresolved",
            confidenceScore: 0.43,
            valueLabel: "Manual hillside confirmation",
            citationLabel: "Hillside overlay check",
            evidenceExcerpt: "Topographic interpretation should be reviewed before Cover gives a final go-forward recommendation.",
          },
        ],
      },
      {
        id: "adu-3",
        label: "ADU / 3 bed",
        buildingType: "ADU",
        bedrooms: 3,
        summary: "Higher program pressure but still commercially attractive.",
        footprintLabel: "1,360 sf",
        heightCap: "24 ft",
        unresolvedLabel: "Parking interpretation",
        narrative: "Added bedrooms keep the parcel attractive but make parking and height assumptions much more important to explain.",
        constraints: [
          {
            domain: "setback",
            provenanceState: "deterministic",
            confidenceScore: 0.92,
            valueLabel: "16 ft front setback envelope",
            citationLabel: "LAMC 12.21",
            evidenceExcerpt: "The base setback shell holds even as the program grows.",
          },
          {
            domain: "parking",
            provenanceState: "interpreted",
            confidenceScore: 0.7,
            valueLabel: "2 stalls likely required",
            citationLabel: "LAMC parking note",
            evidenceExcerpt: "Bedroom increase pushes parking assumptions into a more interpretive zone.",
          },
          {
            domain: "height",
            provenanceState: "deterministic",
            confidenceScore: 0.88,
            valueLabel: "24 ft massing cap",
            citationLabel: "Height envelope",
            evidenceExcerpt: "Height remains feasible but changes the visible envelope profile and homeowner expectation.",
          },
        ],
      },
    ],
  },
  {
    id: "parcel-b",
    label: "Parcel B",
    address: "3908 Glenfeliz Blvd, Los Angeles, CA 90039",
    apn: "5591-004-021",
    neighborhood: "Atwater Village",
    zone: "RS-1",
    overlays: ["Hillside"],
    lotSize: "6,420 sf",
    frontage: "Glenfeliz Blvd hillside edge",
    geocodeConfidence: "ROOFTOP",
    geometry: {
      type: "Polygon",
      coordinates: [[[-118.2748, 34.1165], [-118.2741, 34.1165], [-118.2741, 34.116], [-118.2748, 34.116], [-118.2748, 34.1165]]],
    },
    verdictTitle: "ADU possible, but overlay conflict needs explicit human review",
    verdictDetail: "Great demo parcel for showing state-versus-local conflict handling, because the system surfaces the contradiction instead of hiding it.",
    confidence: 0.71,
    activeConstraints: 4,
    unresolvedItems: 2,
    reviewFocus: "Overlay conflict, slope, ADU precedence",
    nextStep: "Route to architect review before quoting timeline",
    sourceSnapshot: "Verified Mar 22",
    salesNarrative: "This parcel demonstrates why Cover wins: the product explains risk clearly before anyone overpromises.",
    homeownerNarrative: "The lot may still work, but local hillside rules and state ADU law need expert interpretation before a commitment.",
    comparisonTag: "Conflict case",
    scenarios: [
      {
        id: "adu-1",
        label: "ADU / 1 bed",
        buildingType: "ADU",
        bedrooms: 1,
        summary: "Interpretable but not auto-exportable.",
        footprintLabel: "980 sf",
        heightCap: "20 ft",
        unresolvedLabel: "State/local conflict",
        narrative: "This is the archetypal legal-gray-area parcel. It is compelling in demo because the system stays deterministic about what is known and explicit about what is not.",
        constraints: [
          {
            domain: "overlay",
            provenanceState: "interpreted",
            confidenceScore: 0.68,
            valueLabel: "Hillside overlay likely applies",
            citationLabel: "LAMC 12.23",
            evidenceExcerpt: "Overlay geometry intersects the parcel shell and may impose additional design review and setback treatment.",
          },
          {
            domain: "adu-precedence",
            provenanceState: "interpreted",
            confidenceScore: 0.7,
            valueLabel: "State ADU law likely prevails",
            citationLabel: "AB 881 + local conflict note",
            evidenceExcerpt: "Local prohibition and state allowance are shown together so the architect can defend the reasoning path.",
          },
          {
            domain: "height",
            provenanceState: "deterministic",
            confidenceScore: 0.86,
            valueLabel: "35 ft hillside cap",
            citationLabel: "Hillside height rule",
            evidenceExcerpt: "Height cap is lower than the base zone and directly shapes the 3D envelope.",
          },
        ],
      },
      {
        id: "sfh-4",
        label: "SFH / 4 bed",
        buildingType: "SFH",
        bedrooms: 4,
        summary: "Safer than ADU path but still review-heavy.",
        footprintLabel: "1,520 sf",
        heightCap: "35 ft",
        unresolvedLabel: "Slope adjustment",
        narrative: "Single-family massing reduces the state-law conflict but still benefits from a careful overlay explanation.",
        constraints: [
          {
            domain: "setback",
            provenanceState: "deterministic",
            confidenceScore: 0.88,
            valueLabel: "20 ft front / 10 ft hillside edge",
            citationLabel: "RS + Hillside setback",
            evidenceExcerpt: "Additional hillside edge treatment increases the effective envelope margin.",
          },
          {
            domain: "design-review",
            provenanceState: "interpreted",
            confidenceScore: 0.66,
            valueLabel: "Design review likely required",
            citationLabel: "Hillside review guidance",
            evidenceExcerpt: "Planning review trigger is visible and should shape the delivery timeline conversation.",
          },
          {
            domain: "slope",
            provenanceState: "unresolved",
            confidenceScore: 0.49,
            valueLabel: "Survey confirmation recommended",
            citationLabel: "Topographic verification",
            evidenceExcerpt: "A survey-backed slope read would tighten confidence before client signoff.",
          },
        ],
      },
    ],
  },
  {
    id: "parcel-c",
    label: "Parcel C",
    address: "812 N Normandie Ave, Los Angeles, CA 90029",
    apn: "5535-009-014",
    neighborhood: "East Hollywood",
    zone: "RD2",
    overlays: [],
    lotSize: "11,240 sf",
    frontage: "Normandie Ave urban frontage",
    geocodeConfidence: "INTERPOLATED",
    geometry: {
      type: "Polygon",
      coordinates: [[[-118.3006, 34.0847], [-118.2998, 34.0847], [-118.2998, 34.0842], [-118.3006, 34.0842], [-118.3006, 34.0847]]],
    },
    verdictTitle: "High-value density parcel with strong comparison upside",
    verdictDetail: "This is the portfolio parcel: it makes batch comparison and development upside legible for sales and pre-design conversations.",
    confidence: 0.81,
    activeConstraints: 3,
    unresolvedItems: 0,
    reviewFocus: "Density, FAR, guest house path",
    nextStep: "Use comparison sheet to position Cover against manual research",
    sourceSnapshot: "Verified Mar 22",
    salesNarrative: "Excellent for showing that Cover is not just an ADU checker; it helps frame broader buildability and density conversations.",
    homeownerNarrative: "This site has more development flexibility than a typical single-family parcel, which may open additional options.",
    comparisonTag: "Portfolio upside",
    scenarios: [
      {
        id: "guest-house",
        label: "Guest house / 2 bed",
        buildingType: "Guest House",
        bedrooms: 2,
        summary: "Shows denser-zone flexibility clearly.",
        footprintLabel: "1,480 sf",
        heightCap: "55 ft",
        unresolvedLabel: "No open item",
        narrative: "This parcel proves the system can reason beyond the simplest RS-only case and still stay explainable.",
        constraints: [
          {
            domain: "density",
            provenanceState: "deterministic",
            confidenceScore: 0.9,
            valueLabel: "3 units per 5,000 sf density baseline",
            citationLabel: "LAMC 12.20",
            evidenceExcerpt: "RD2 density logic increases the development conversation beyond a one-unit mindset.",
          },
          {
            domain: "setback",
            provenanceState: "deterministic",
            confidenceScore: 0.86,
            valueLabel: "20 ft front / 0 ft side / 15 ft rear",
            citationLabel: "RD2 setback rule",
            evidenceExcerpt: "Flexible side yard treatment materially changes the buildable footprint.",
          },
          {
            domain: "far",
            provenanceState: "deterministic",
            confidenceScore: 0.89,
            valueLabel: "1.3 FAR guidance",
            citationLabel: "RD2 FAR note",
            evidenceExcerpt: "FAR capacity supports a stronger comparison narrative against smaller single-family parcels.",
          },
        ],
      },
    ],
  },
  {
    id: "parcel-d",
    label: "Parcel D",
    address: "2450 Ocean Front Walk, Los Angeles, CA 90291",
    apn: "4226-017-033",
    neighborhood: "Venice",
    zone: "RD2",
    overlays: ["Coastal Zone"],
    lotSize: "12,180 sf",
    frontage: "Ocean-facing frontage",
    geocodeConfidence: "ROOFTOP",
    geometry: {
      type: "Polygon",
      coordinates: [[[-118.4684, 33.9854], [-118.4676, 33.9854], [-118.4676, 33.9849], [-118.4684, 33.9849], [-118.4684, 33.9854]]],
    },
    verdictTitle: "Premium parcel with strong value and strong caution",
    verdictDetail: "Best parcel for showing why Cover matters in high-stakes conversations: a visually attractive project with real regulatory nuance.",
    confidence: 0.69,
    activeConstraints: 4,
    unresolvedItems: 2,
    reviewFocus: "Coastal review, parking, view protection",
    nextStep: "Escalate to architect + planning consultant before homeowner promise",
    sourceSnapshot: "Verified Mar 22",
    salesNarrative: "Great executive demo parcel because it combines premium upside with obvious need for a defensible workflow.",
    homeownerNarrative: "The property has real potential, but the coastal overlay introduces review requirements that should be handled carefully and transparently.",
    comparisonTag: "Premium caution",
    scenarios: [
      {
        id: "adu-1",
        label: "ADU / 1 bed",
        buildingType: "ADU",
        bedrooms: 1,
        summary: "Potentially viable with layered review caveats.",
        footprintLabel: "1,020 sf",
        heightCap: "55 ft / coastal adjusted",
        unresolvedLabel: "Coastal interpretation",
        narrative: "This parcel makes the client-handoff story powerful because the system keeps the recommendation exciting but grounded.",
        constraints: [
          {
            domain: "overlay",
            provenanceState: "interpreted",
            confidenceScore: 0.67,
            valueLabel: "Coastal review likely governs final envelope",
            citationLabel: "LAMC 12.20.1",
            evidenceExcerpt: "Coastal protections may change the practical envelope even where the base zone remains permissive.",
          },
          {
            domain: "parking",
            provenanceState: "interpreted",
            confidenceScore: 0.64,
            valueLabel: "Parking relief uncertain",
            citationLabel: "Coastal parking note",
            evidenceExcerpt: "State ADU flexibility and coastal parking conditions should be reviewed together, not separately.",
          },
          {
            domain: "view-protection",
            provenanceState: "unresolved",
            confidenceScore: 0.48,
            valueLabel: "Manual coastal review advised",
            citationLabel: "View protection trigger",
            evidenceExcerpt: "A high-stakes design conversation should include coastal view protection analysis before commitment.",
          },
        ],
      },
    ],
  },
];
