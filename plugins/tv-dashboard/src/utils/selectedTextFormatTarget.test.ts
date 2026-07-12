import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import {
  isChartTextFormatPart,
  isKpiTextFormatPart,
  resolveSelectedTextFormatTarget,
} from "./selectedTextFormatTarget";

const textBlock = {
  id: "t1",
  type: "text",
  frame: { x: 0, y: 0, w: 20, h: 10 },
  content: "Olá",
  style: { fontFamily: "Inter", fontSize: 28, color: "#111" },
} as ComunicadoBlock;

const kpiBlock = {
  id: "k1",
  type: "kpi_view",
  frame: { x: 0, y: 0, w: 30, h: 30 },
  dataSourceId: "ds1",
  kpiParts: {
    title: { style: { fontSize: 14, color: "#334155", fontFamily: "Inter" } },
  },
} as ComunicadoBlock;

const chartBlock = {
  id: "c1",
  type: "chart_view",
  frame: { x: 0, y: 0, w: 40, h: 40 },
  dataSourceId: "ds1",
  chartType: "bar",
  chartParts: {
    title: { style: { fontSize: 16, fontWeight: "bold", color: "#0f172a" } },
  },
} as ComunicadoBlock;

describe("selectedTextFormatTarget", () => {
  it("reconhece partes textuais de KPI e chart", () => {
    expect(isKpiTextFormatPart({ kind: "title" })).toBe(true);
    expect(isKpiTextFormatPart({ kind: "card" })).toBe(false);
    expect(isChartTextFormatPart({ kind: "title" })).toBe(true);
    expect(isChartTextFormatPart({ kind: "series", seriesIndex: 0 })).toBe(false);
  });

  it("resolve bloco text/heading", () => {
    const target = resolveSelectedTextFormatTarget({ selected: textBlock });
    expect(target?.mode).toBe("block");
    if (target?.mode === "block") {
      expect(target.style.fontSize).toBe(28);
    }
  });

  it("resolve parte título do KPI", () => {
    const target = resolveSelectedTextFormatTarget({
      selected: kpiBlock,
      selectedKpiPart: { kind: "title" },
    });
    expect(target?.mode).toBe("part");
    if (target?.mode === "part") {
      expect(target.source).toBe("kpi");
      expect(target.style.fontSize).toBe(14);
      expect(target.style.color).toBe("#334155");
    }
  });

  it("resolve parte título do gráfico", () => {
    const target = resolveSelectedTextFormatTarget({
      selected: chartBlock,
      selectedChartPart: { kind: "title" },
    });
    expect(target?.mode).toBe("part");
    if (target?.mode === "part") {
      expect(target.source).toBe("chart");
      expect(target.style.fontWeight).toBe("bold");
    }
  });

  it("não resolve tipografia quando KPI está no card", () => {
    expect(
      resolveSelectedTextFormatTarget({
        selected: kpiBlock,
        selectedKpiPart: { kind: "card" },
      }),
    ).toBeNull();
  });
});
