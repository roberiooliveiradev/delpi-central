// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MyWegNeedsHistoryChart } from "./MyWegNeedsHistoryChart";
import type { MyWegNeedsBatchSummary } from "../types";

const onCategoryClick = vi.fn();

vi.mock("@delpi/plugin-ui/index", () => ({
  CHART_COLORS_DEPARTMENTAL: ["#089bdb", "#003866", "#5b8def", "#7aa2f7", "#9ec1ff", "#b7d0ff"],
  MultiTypeSeriesChart: ({
    data,
    onCategoryClick: onClick,
  }: {
    data: Array<{ label: string; batchId: string }>;
    onCategoryClick?: (category: string) => void;
  }) => (
    <div data-testid="series-chart">
      {data.map((row) => (
        <button
          key={row.batchId}
          type="button"
          onClick={() => onClick?.(row.label)}
        >
          {row.label}
        </button>
      ))}
    </div>
  ),
  ChartCard: ({ title, children }: { title: string; children: ReactNode }) => (
    <section>
      <h2>{title}</h2>
      {children}
    </section>
  ),
  chartCardBemClasses: () => ({}),
}));

vi.mock("./ChartCard", () => ({
  ChartCard: ({ title, children }: { title: string; children: ReactNode }) => (
    <section>
      <h2>{title}</h2>
      {children}
    </section>
  ),
}));

const items: MyWegNeedsBatchSummary[] = [
  {
    id: "batch-a",
    collectionId: "c-a",
    branch: "02",
    status: "accepted",
    collectedAt: "2026-11-03T10:00:00-03:00",
    collectionDate: "2026-11-03",
    importedAt: "2026-11-03T10:05:00-03:00",
    recordCount: 10,
    totals: { quantidade_original_un: "40", quantidade_mi: "1" },
  },
  {
    id: "batch-b",
    collectionId: "c-b",
    branch: "02",
    status: "accepted",
    collectedAt: "2026-11-05T10:00:00-03:00",
    collectionDate: "2026-11-05",
    importedAt: "2026-11-05T10:05:00-03:00",
    recordCount: 20,
    totals: { quantidade_original_un: "90", quantidade_mi: "2" },
  },
];

describe("MyWegNeedsHistoryChart", () => {
  afterEach(() => {
    cleanup();
    onCategoryClick.mockReset();
  });

  it("renderiza barras clicáveis e select acessível", () => {
    render(
      <MyWegNeedsHistoryChart
        items={items}
        selectedBatchId="batch-b"
        latestBatchId="batch-b"
        onSelectBatch={onCategoryClick}
      />,
    );

    expect(screen.getByRole("heading", { name: /histórico de coletas/i })).toBeTruthy();
    expect(screen.getByTestId("series-chart")).toBeTruthy();

    fireEvent.click(screen.getByTestId("series-chart").querySelector("button")!);
    expect(onCategoryClick).toHaveBeenCalledWith("batch-a");

    fireEvent.change(screen.getByRole("combobox", { name: /selecionar coleta MyWEG/i }), {
      target: { value: "batch-a" },
    });
    expect(onCategoryClick).toHaveBeenCalledWith("batch-a");
  });

  it("mostra estado vazio sem itens", () => {
    render(
      <MyWegNeedsHistoryChart
        items={[]}
        selectedBatchId={null}
        latestBatchId={null}
        onSelectBatch={onCategoryClick}
      />,
    );
    expect(screen.getByText(/sem histórico de coletas/i)).toBeTruthy();
  });
});
