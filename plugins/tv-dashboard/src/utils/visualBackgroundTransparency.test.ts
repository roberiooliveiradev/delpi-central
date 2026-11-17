import { describe, expect, it } from "vitest";
import {
  resolveChartAreaStyle,
  resolvePlotAreaStyle,
  resolveTableFrameStyle,
  type ComunicadoChartViewBlock,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  chartBackgroundTransparencyPatch,
  isChartBackgroundTransparent,
  isTableBackgroundTransparent,
  tableBackgroundTransparencyPatch,
} from "./visualBackgroundTransparency";

function chartBlock(): ComunicadoChartViewBlock {
  return {
    id: "chart-1606",
    type: "chart_view",
    frame: { x: 0, y: 0, w: 100, h: 100 },
    chartType: "bar",
    chartOptions: {
      title: "Evolução mensal de divergências",
      showLegend: true,
      backgroundColor: "#fefefe",
      seriesColor: "#089bdb",
    },
    chartParts: {
      chartArea: {
        style: { fill: "#fefefe", stroke: "#009fe3", strokeWidth: 1, boxShadow: "none" },
      },
      plotArea: { style: { fill: "#ffffff", strokeWidth: 0 } },
      title: { style: { color: "#111111", fontSize: 19 } },
      legend: { visible: true },
    },
  } as ComunicadoChartViewBlock;
}

function tableBlock(): ComunicadoTableViewBlock {
  return {
    id: "table-1606",
    type: "table_view",
    frame: { x: 0, y: 0, w: 100, h: 100 },
    tableOptions: { headerBg: "#dbeafe", cellBg: "#fff8ee", showHeader: true },
    tableParts: {
      frame: { style: { fill: "#ffffff", stroke: "#089bdb", strokeWidth: 1 } },
      headerCell: { style: { fill: "#22c55e" } },
    },
  } as unknown as ComunicadoTableViewBlock;
}

describe("GLPI #1606: fundos visuais transparentes", () => {
  it("remove os dois fundos do gráfico sem alterar as séries, título ou contorno", () => {
    const block = chartBlock();
    const patch = chartBackgroundTransparencyPatch(block, true);
    const result = { ...block, ...patch };
    expect(patch.chartOptions.backgroundColor).toBe("transparent");
    expect(patch.chartParts.chartArea?.style?.fill).toBe("transparent");
    expect(patch.chartParts.plotArea?.style?.fill).toBe("transparent");
    expect(isChartBackgroundTransparent(result)).toBe(true);
    expect(resolveChartAreaStyle(patch.chartOptions, patch.chartParts).fill).toBe("transparent");
    expect(resolvePlotAreaStyle(patch.chartParts).fill).toBe("transparent");
    expect(patch.chartParts.title?.style?.fontSize).toBe(19);
    expect(patch.chartParts.chartArea?.style?.stroke).toBe("#009fe3");
    expect(patch.chartOptions.showLegend).toBe(true);
    expect(block.chartParts?.chartArea?.style?.fill).toBe("#fefefe");
  });

  it("volta ao fundo padrão sem descartar os dados, a legenda e as cores das séries", () => {
    const first = { ...chartBlock(), ...chartBackgroundTransparencyPatch(chartBlock(), true) };
    const second = { ...first, ...chartBackgroundTransparencyPatch(first, false) };
    expect(isChartBackgroundTransparent(first)).toBe(true);
    expect(isChartBackgroundTransparent(second)).toBe(false);
    expect(second.chartParts.chartArea?.style?.fill).not.toBe("transparent");
    expect(second.chartParts.plotArea?.style?.fill).not.toBe("transparent");
    expect(second.chartOptions.seriesColor).toBe("#089bdb");
    expect(second.chartOptions.title).toBe("Evolução mensal de divergências");
  });

  it("tabela preserva as cores internas e torna a moldura transparente", () => {
    const block = tableBlock();
    const patch = tableBackgroundTransparencyPatch(block, true);
    const transparent = { ...block, ...patch };
    expect(isTableBackgroundTransparent(transparent)).toBe(true);
    expect(resolveTableFrameStyle(patch.tableParts).fill).toBe("transparent");
    expect(resolveTableFrameStyle(patch.tableParts).visible).toBe(false);
    expect(transparent.tableOptions.headerBg).toBe("#dbeafe");
    expect(transparent.tableOptions.cellBg).toBe("#fff8ee");
    expect(patch.tableParts.frame?.style?.stroke).toBe("#089bdb");

    const restored = { ...transparent, ...tableBackgroundTransparencyPatch(transparent, false) };
    expect(isTableBackgroundTransparent(restored)).toBe(false);
    expect(resolveTableFrameStyle(restored.tableParts).visible).toBe(true);
    expect(restored.tableOptions.headerBg).toBe("#dbeafe");
  });

  it("uma tela legada não assume transparência automaticamente", () => {
    expect(isChartBackgroundTransparent(chartBlock())).toBe(false);
    expect(isTableBackgroundTransparent(tableBlock())).toBe(false);
  });
});
