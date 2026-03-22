import "@testing-library/jest-dom/vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { demoParcels } from "../../data/demoStudio";
import { AssessmentWorkspace } from "./AssessmentWorkspace";

describe("AssessmentWorkspace", () => {
  it("shows provenance-aware constraints in the default state", () => {
    render(<AssessmentWorkspace parcel={demoParcels[0]} audienceMode="architect" />);

    expect(screen.getByText("Architect review packet")).toBeInTheDocument();
    expect(screen.getAllByText("deterministic").length).toBeGreaterThan(0);
    expect(screen.getByText("Constraint details")).toBeInTheDocument();
  });

  it("switches to 3D mode and shows a scenario diff when the scenario changes", async () => {
    const user = userEvent.setup();
    render(<AssessmentWorkspace parcel={demoParcels[0]} audienceMode="architect" />);

    const visualizationStage = document.getElementById("visualization-stage");
    if (!visualizationStage) {
      throw new Error("Visualization stage not found");
    }
    const scenarioPanel = document.getElementById("scenario-panel");
    if (!scenarioPanel) {
      throw new Error("Scenario panel not found");
    }

    await user.click(within(visualizationStage).getByRole("button", { name: "3D" }));
    await user.click(within(scenarioPanel).getByRole("button", { name: /ADU \/ 3 bed/i }));

    expect(screen.getByText(/3D view shows a massing read/i)).toBeInTheDocument();
    expect(within(scenarioPanel).getByText("2 stalls likely required")).toBeInTheDocument();
  });
});
