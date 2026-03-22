import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ParcelLookupWorkspace } from "./ParcelLookupWorkspace";

vi.mock("../../components/map/ParcelMap", () => ({
  ParcelMap: () => <div data-testid="parcel-map">Map stub</div>,
}));

describe("ParcelLookupWorkspace", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("shows the rooftop accuracy flag in the ready state", () => {
    render(<ParcelLookupWorkspace />);

    expect(screen.getByTestId("accuracy-flag")).toHaveTextContent("ROOFTOP");
    expect(screen.getAllByText("1321 Lucile Ave, Los Angeles, CA 90026").length).toBeGreaterThan(0);
  });

  it("preserves orientation and shows a recoverable message if lookup fails", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
      }),
    );

    render(<ParcelLookupWorkspace />);
    await user.clear(screen.getByLabelText("Address or APN"));
    await user.type(screen.getByLabelText("Address or APN"), "1 Failed Lookup Ave");
    await user.click(screen.getByRole("button", { name: "Locate parcel" }));

    expect(screen.getByText(/Live parcel services are unavailable right now/)).toBeInTheDocument();
    expect(screen.getByTestId("accuracy-flag")).toHaveTextContent("ROOFTOP");
    expect(screen.getByTestId("parcel-map")).toBeInTheDocument();
  });
});
