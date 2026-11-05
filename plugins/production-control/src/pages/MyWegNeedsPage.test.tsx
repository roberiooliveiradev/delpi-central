// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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
    latest: {
      id: "batch-latest",
      collectedAt: "2026-11-05T05:00:20-03:00",
      recordCount: 496,
      collectionDate: "2026-11-05",
      totals: { quantidade_original_un: "100", quantidade_mi: "0.1" },
    },
    selected: {
      id: "batch-latest",
      collectedAt: "2026-11-05T05:00:20-03:00",
      recordCount: 496,
      collectionDate: "2026-11-05",
      totals: { quantidade_original_un: "100", quantidade_mi: "0.1" },
    },
    history: {
      items: [
        {
          id: "batch-latest",
          collectedAt: "2026-11-05T05:00:20-03:00",
          recordCount: 496,
          collectionDate: "2026-11-05",
        },
        {
          id: "batch-prev",
          collectedAt: "2026-11-04T14:28:27-03:00",
          recordCount: 532,
          collectionDate: "2026-11-04",
        },
      ],
    },
    items: { items: [], page: 1, pageSize: 50, total: 0 },
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

vi.mock("../components/MyWegPlanningEvolutionPanel", () => ({
  MyWegPlanningEvolutionPanel: () => (
    <div data-testid="myweg-compare-panel">compare-panel</div>
  ),
}));

vi.mock("@delpi/plugin-ui/index", () => ({
  createDashboardLoadingActivityCard: () => () => null,
  DelpiLogoMark: () => null,
  HelpTooltip: () => null,
}));

describe("MyWegNeedsPage", () => {
  afterEach(() => {
    cleanup();
  });

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
        view={null}
        analysis={null}
      />,
    );
    expect(screen.getByText(/somente na filial 02/i)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /abrir filial 02/i }));
    expect(navigatePpc).toHaveBeenCalled();
    const href = String(navigatePpc.mock.calls[0]?.[0] ?? "");
    expect(href).toContain("branch=02");
    expect(href).toContain("/myweg-needs");
  });

  it("mostra consulta por padrão e não monta comparação", () => {
    render(
      <MyWegNeedsPage
        branch="02"
        batchId={null}
        search={null}
        remessaFrom={null}
        remessaTo={null}
        page={null}
        view={null}
        analysis={null}
      />,
    );
    expect(screen.getByRole("heading", { name: /consulta da coleta/i })).toBeTruthy();
    expect(screen.queryByTestId("myweg-compare-panel")).toBeNull();
  });

  it("card Comparar coletas navega para view=compare", () => {
    render(
      <MyWegNeedsPage
        branch="02"
        batchId={null}
        search={null}
        remessaFrom={null}
        remessaTo={null}
        page={null}
        view={null}
        analysis={null}
      />,
    );
    const compareCards = screen.getAllByRole("button", {
      name: /comparação entre coletas/i,
    });
    fireEvent.click(compareCards[0]);
    expect(navigatePpc).toHaveBeenCalled();
    const href = String(navigatePpc.mock.calls[0]?.[0] ?? "");
    expect(href).toContain("view=compare");
  });

  it("view=compare monta o painel e esconde a tabela de necessidades", () => {
    const { queryByTestId, getByTestId } = render(
      <MyWegNeedsPage
        branch="02"
        batchId={null}
        search={null}
        remessaFrom={null}
        remessaTo={null}
        page={null}
        view="compare"
        analysis={null}
      />,
    );
    expect(getByTestId("myweg-compare-panel")).toBeTruthy();
    expect(queryByTestId("myweg-needs-table")).toBeNull();
  });
});
