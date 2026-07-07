import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ChartGranularityToggle, ChartToolbar, chartToolbarBemClasses } from "./ChartToolbar";

const OPTIONS = [
  { value: "day", label: "Dia" },
  { value: "month", label: "Mês" },
] as const;

const bem = chartToolbarBemClasses("dp");
const labels = {
  groupAriaLabel: "Agrupamento do gráfico",
  exportSeries: "Exportar série",
  exportSeriesAriaLabel: "Exportar série do gráfico em CSV",
};

describe("ChartGranularityToggle", () => {
  it("marca botão ativo", () => {
    render(
      <ChartGranularityToggle
        value="day"
        onChange={() => undefined}
        options={OPTIONS}
        classNames={{
          root: bem.segmentToggle,
          button: bem.segmentButton,
          buttonActive: bem.segmentButtonActive,
        }}
        labels={labels}
      />,
    );

    expect(screen.getByRole("button", { name: "Dia" }).getAttribute("aria-pressed")).toBe("true");
  });
});

describe("ChartToolbar", () => {
  it("renderiza exportação CSV quando informada", () => {
    render(
      <ChartToolbar
        granularity="day"
        onGranularityChange={() => undefined}
        options={OPTIONS}
        onExportCsv={vi.fn()}
        classNames={{
          toolbar: bem.toolbar,
          actions: bem.actions,
          exportButton: bem.exportButton,
        }}
        labels={labels}
        granularityToggleClassNames={{
          root: bem.segmentToggle,
          button: bem.segmentButton,
          buttonActive: bem.segmentButtonActive,
        }}
        granularityToggleLabels={labels}
      />,
    );

    expect(screen.getByRole("button", { name: labels.exportSeriesAriaLabel })).toBeTruthy();
  });
});
