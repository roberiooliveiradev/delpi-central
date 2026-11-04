// @vitest-environment jsdom

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MyWegNeedsPage } from "./MyWegNeedsPage";

const navigatePpc = vi.fn();
const reload = vi.fn();

vi.mock("../utils/routeParser", async () => {
  const actual = await vi.importActual<typeof import("../utils/routeParser")>(
    "../utils/routeParser",
  );
  return {
    ...actual,
    navigatePpc: (...args: unknown[]) => navigatePpc(...args),
  };
});

vi.mock("../hooks/useMyWegNeeds", () => ({
  useMyWegNeeds: () => ({
    latest: null,
    selected: null,
    history: null,
    items: null,
    loading: false,
    refreshing: false,
    error: null,
    status: null,
    reload,
  }),
}));

vi.mock("../components/dataTableUi", () => ({
  DataTableSection: () => null,
}));

vi.mock("@delpi/plugin-ui/index", () => ({
  createDashboardLoadingActivityCard: () => () => null,
  DelpiLogoMark: () => null,
  HelpTooltip: () => null,
}));

describe("MyWegNeedsPage", () => {
  beforeEach(() => {
    navigatePpc.mockReset();
    reload.mockReset();
  });

  it("AC-02: filial 01 não consulta e oferece ação explícita para a 02", () => {
    render(
      <MyWegNeedsPage
        branch="01"
        batchId={null}
        search={null}
        remessaFrom={null}
        remessaTo={null}
        page={null}
      />,
    );
    expect(screen.getByText(/somente na filial 02/i)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /abrir filial 02/i }));
    expect(navigatePpc).toHaveBeenCalled();
    const href = String(navigatePpc.mock.calls[0]?.[0] ?? "");
    expect(href).toContain("branch=02");
    expect(href).toContain("/myweg-needs");
  });
});
