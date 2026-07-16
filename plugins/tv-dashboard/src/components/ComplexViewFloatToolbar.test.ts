import { describe, expect, it } from "vitest";

import { shouldShowComplexViewFloatToolbar } from "../components/ComplexViewFloatToolbar";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

function chartBlock(): ComunicadoBlock {
  return {
    id: "c1",
    type: "chart_view",
    chartType: "line",
    frame: { x: 0, y: 0, w: 40, h: 30 },
    style: { zIndex: 1 },
  } as ComunicadoBlock;
}

function kpiBlock(): ComunicadoBlock {
  return {
    id: "k1",
    type: "kpi_view",
    frame: { x: 0, y: 0, w: 20, h: 15 },
    style: { zIndex: 1 },
  } as ComunicadoBlock;
}

function tableBlock(): ComunicadoBlock {
  return {
    id: "t1",
    type: "table_view",
    tablePreset: "grid",
    frame: { x: 0, y: 0, w: 40, h: 30 },
    style: { zIndex: 1 },
  } as ComunicadoBlock;
}

describe("shouldShowComplexViewFloatToolbar", () => {
  it("mostra float em chart/kpi/table sem parte selecionada", () => {
    expect(
      shouldShowComplexViewFloatToolbar({
        block: chartBlock(),
        isPrimary: true,
        selectedIdsLength: 1,
        selectedChartPart: null,
        selectedKpiPart: null,
        selectedTablePart: null,
      }),
    ).toBe(true);
    expect(
      shouldShowComplexViewFloatToolbar({
        block: kpiBlock(),
        isPrimary: true,
        selectedIdsLength: 1,
        selectedChartPart: null,
        selectedKpiPart: null,
        selectedTablePart: null,
      }),
    ).toBe(true);
    expect(
      shouldShowComplexViewFloatToolbar({
        block: tableBlock(),
        isPrimary: true,
        selectedIdsLength: 1,
        selectedChartPart: null,
        selectedKpiPart: null,
        selectedTablePart: null,
      }),
    ).toBe(true);
  });

  it("oculta com parte selecionada ou multi-seleção", () => {
    expect(
      shouldShowComplexViewFloatToolbar({
        block: chartBlock(),
        isPrimary: true,
        selectedIdsLength: 1,
        selectedChartPart: { kind: "legend" },
        selectedKpiPart: null,
        selectedTablePart: null,
      }),
    ).toBe(false);
    expect(
      shouldShowComplexViewFloatToolbar({
        block: kpiBlock(),
        isPrimary: true,
        selectedIdsLength: 1,
        selectedChartPart: null,
        selectedKpiPart: { kind: "value" },
        selectedTablePart: null,
      }),
    ).toBe(false);
    expect(
      shouldShowComplexViewFloatToolbar({
        block: tableBlock(),
        isPrimary: true,
        selectedIdsLength: 2,
        selectedChartPart: null,
        selectedKpiPart: null,
        selectedTablePart: null,
      }),
    ).toBe(false);
  });
});
