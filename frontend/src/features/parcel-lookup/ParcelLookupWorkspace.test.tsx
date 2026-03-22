import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { demoParcels } from "../../data/demoStudio";
import { ParcelLookupWorkspace } from "./ParcelLookupWorkspace";

vi.mock("../../components/map/ParcelMap", () => ({
  ParcelMap: () => <div data-testid="parcel-map">Map stub</div>,
}));

describe("ParcelLookupWorkspace", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows the selected parcel context and rooftop accuracy flag", () => {
    render(<ParcelLookupWorkspace parcels={demoParcels} selectedParcelId="parcel-a" onSelectParcel={vi.fn()} />);

    expect(screen.getByTestId("accuracy-flag")).toHaveTextContent("ROOFTOP");
    expect(screen.getByText("Map-first parcel review")).toBeInTheDocument();
    expect(screen.getAllByText("1321 Lucile Ave, Los Angeles, CA 90026").length).toBeGreaterThan(0);
  });

  it("switches the active parcel from the comparison surface", async () => {
    const user = userEvent.setup();
    const onSelectParcel = vi.fn();

    render(<ParcelLookupWorkspace parcels={demoParcels} selectedParcelId="parcel-a" onSelectParcel={onSelectParcel} />);
    await user.click(screen.getByRole("button", { name: /parcel c/i }));

    expect(onSelectParcel).toHaveBeenCalledWith("parcel-c");
    expect(screen.getByTestId("parcel-map")).toBeInTheDocument();
  });
});
