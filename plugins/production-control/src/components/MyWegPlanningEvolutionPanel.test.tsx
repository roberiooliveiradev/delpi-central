// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MyWegPlanningEvolutionPanel } from "./MyWegPlanningEvolutionPanel";
import type { MyWegNeedsBatchSummary } from "../types";

const onAnalysisChange = vi.fn();

vi.mock("@delpi/plugin-ui/index", () => ({
  createDashboardKpiCard: () =>
    function Kpi({ title, value }: { title: string; value: string }) {
      return (
        <div data-testid={`kpi-${title}`}>
          <span>{title}</span>
          <strong>{value}</strong>
        </div>
      );
    },
  HelpTooltip: () => null,
}));

vi.mock("../api/ppcApi", () => ({
  fetchMyWegNeedBatchesCompare: vi.fn(() =>
    Promise.resolve({
      scope: {
        customerName: "WEG",
        protheusCustomerCode: "001",
        protheusCustomerStore: "01",
      },
      fromBatch: { id: "batch-prev", collectionDate: "2026-11-04" },
      toBatch: { id: "batch-latest", collectionDate: "2026-11-05" },
      page: 1,
      pageSize: 50,
      total: 0,
      totalCompared: 10,
      totalChanges: 4,
      items: [],
      observed: {
        summary: {
          increased: 1,
          decreased: 2,
          appeared: 3,
          disappeared: 4,
          horizon_14d_changes: 5,
        },
        probableDateShifts: [],
        referenceDate: "2026-11-05",
      },
      billing: { status: "skipped" },
    }),
  ),
}));

vi.mock("./dataTableUi", () => ({
  DataTableSection: () => <div>table</div>,
}));

vi.mock("./MyWegProbableDateShiftsSection", () => ({
  MyWegProbableDateShiftsSection: () => <div data-testid="shifts">shifts</div>,
}));

vi.mock("./MyWegProductConsolidationPanel", () => ({
  MyWegProductConsolidationPanel: () => (
    <div data-testid="products-panel">products</div>
  ),
}));

const historyItems: MyWegNeedsBatchSummary[] = [
  {
    id: "batch-latest",
    collectionId: "c-l",
    branch: "02",
    status: "accepted",
    collectedAt: "2026-11-05T05:00:20-03:00",
    collectionDate: "2026-11-05",
    importedAt: "2026-11-05T05:05:00-03:00",
    recordCount: 496,
    totals: { quantidade_original_un: "100", quantidade_mi: "0.1" },
  },
  {
    id: "batch-prev",
    collectionId: "c-p",
    branch: "02",
    status: "accepted",
    collectedAt: "2026-11-04T14:28:27-03:00",
    collectionDate: "2026-11-04",
    importedAt: "2026-11-04T14:30:00-03:00",
    recordCount: 532,
    totals: { quantidade_original_un: "180", quantidade_mi: "0.2" },
  },
];

describe("MyWegPlanningEvolutionPanel", () => {
  afterEach(() => {
    cleanup();
    onAnalysisChange.mockReset();
  });

  it("renderiza cards de análise e card de filtros no estilo mock", async () => {
    render(
      <MyWegPlanningEvolutionPanel
        historyItems={historyItems}
        selectedBatchId="batch-latest"
        analysis="remessa"
        onAnalysisChange={onAnalysisChange}
      />,
    );

    expect(
      screen.getByRole("button", { name: /^Por remessa —/i }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: /^Por produto —/i }),
    ).toBeTruthy();
    expect(screen.getByRole("heading", { name: /filtros da comparação/i })).toBeTruthy();
    expect(await screen.findByTestId("kpi-Aumentos")).toBeTruthy();
    expect(screen.getByTestId("kpi-Reduções")).toBeTruthy();
    expect(screen.getByTestId("shifts")).toBeTruthy();
    expect(screen.queryByTestId("myweg-compare-table")).toBeNull();
  });

  it("card Por produto troca a análise", () => {
    render(
      <MyWegPlanningEvolutionPanel
        historyItems={historyItems}
        selectedBatchId="batch-latest"
        analysis="remessa"
        onAnalysisChange={onAnalysisChange}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /^Por produto —/i }));
    expect(onAnalysisChange).toHaveBeenCalledWith("products");
  });

  it("analysis=products monta o painel consolidado", () => {
    render(
      <MyWegPlanningEvolutionPanel
        historyItems={historyItems}
        selectedBatchId="batch-latest"
        analysis="products"
        onAnalysisChange={onAnalysisChange}
      />,
    );
    expect(screen.getByTestId("products-panel")).toBeTruthy();
  });
});
