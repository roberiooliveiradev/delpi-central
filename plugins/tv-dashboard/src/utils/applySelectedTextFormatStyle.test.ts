import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { buildSelectedTextFormatBlockPatch } from "./applySelectedTextFormatStyle";

describe("buildSelectedTextFormatBlockPatch", () => {
  it("tipografia global da tabela grava tableOptions", () => {
    const selected = {
      id: "tb1",
      type: "table_view",
      frame: { x: 0, y: 0, w: 40, h: 30 },
      tableOptions: { fontSize: 14 },
    } as ComunicadoBlock;
    const patch = buildSelectedTextFormatBlockPatch({
      selected,
      patch: { fontFamily: "Georgia, serif", fontSize: 20, color: "#112233", textAlign: "center" },
    });
    expect(patch?.tableOptions).toMatchObject({
      fontFamily: "Georgia, serif",
      fontSize: 20,
      cellTextColor: "#112233",
      headerTextColor: "#112233",
      textAlign: "center",
    });
  });

  it("tipografia global do gráfico replica nas partes textuais", () => {
    const selected = {
      id: "c1",
      type: "chart_view",
      chartType: "bar",
      frame: { x: 0, y: 0, w: 40, h: 30 },
      chartParts: {},
    } as ComunicadoBlock;
    const patch = buildSelectedTextFormatBlockPatch({
      selected,
      patch: { fontSize: 18, color: "#0f172a", fontWeight: "bold" },
    });
    expect(patch?.chartParts?.title?.style?.fontSize).toBe(18);
    expect(patch?.chartParts?.legend?.style?.color).toBe("#0f172a");
    expect(patch?.chartParts?.["axis:x"]?.style?.fontWeight).toBe("bold");
  });

  it("parte Eixos altera só axis:x/y e não dataLabels/título/legenda", () => {
    const selected = {
      id: "c1",
      type: "chart_view",
      chartType: "bar",
      frame: { x: 0, y: 0, w: 40, h: 30 },
      chartParts: {
        dataLabels: { style: { fontSize: 12 } },
        title: { style: { fontSize: 22 } },
        legend: { style: { fontSize: 16 } },
      },
    } as ComunicadoBlock;
    const patch = buildSelectedTextFormatBlockPatch({
      selected,
      selectedChartPart: { kind: "axes" },
      patch: { fontSize: 35 },
    });
    expect(patch?.chartParts?.["axis:x"]?.style?.fontSize).toBe(35);
    expect(patch?.chartParts?.["axis:y"]?.style?.fontSize).toBe(35);
    expect(patch?.chartParts?.dataLabels?.style?.fontSize).toBe(12);
    expect(patch?.chartParts?.title?.style?.fontSize).toBe(22);
    expect(patch?.chartParts?.legend?.style?.fontSize).toBe(16);
  });

  it("tipografia global do KPI replica title/value/hint", () => {
    const selected = {
      id: "k1",
      type: "kpi_view",
      frame: { x: 0, y: 0, w: 20, h: 20 },
      dataSourceId: "ds",
      kpiParts: {},
    } as ComunicadoBlock;
    const patch = buildSelectedTextFormatBlockPatch({
      selected,
      patch: { fontFamily: "Inter", color: "#334155" },
    });
    expect(patch?.kpiParts?.title?.style?.fontFamily).toBe("Inter");
    expect(patch?.kpiParts?.value?.style?.color).toBe("#334155");
  });
});
