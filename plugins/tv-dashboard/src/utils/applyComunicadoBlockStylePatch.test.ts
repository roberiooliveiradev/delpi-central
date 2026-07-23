import { describe, expect, it } from "vitest";

import {
  createChartViewBlock,
  createInputBlock,
  createKpiViewBlock,
  createShapeBlock,
  getChartPartState,
  getInputPartState,
  getKpiPartState,
} from "@delpi/tv-dashboard-presentation";

import { applyComunicadoBlockStylePatch } from "./applyComunicadoBlockStylePatch";

describe("applyComunicadoBlockStylePatch", () => {
  it("remove boxShadow ao limpar (undefined / string vazia) em qualquer bloco", () => {
    const shape = {
      ...createShapeBlock("rectangle"),
      style: { zIndex: 2, boxShadow: "0 4px 14px rgba(0, 0, 0, 0.28)" },
    };
    expect(applyComunicadoBlockStylePatch(shape, { boxShadow: undefined }).style?.boxShadow).toBeUndefined();
    expect(applyComunicadoBlockStylePatch(shape, { boxShadow: "" }).style?.boxShadow).toBeUndefined();

    const kpi = {
      ...createKpiViewBlock(),
      style: { zIndex: 2, boxShadow: "0 8px 24px rgba(0, 0, 0, 0.35)" },
    };
    const kpiNext = applyComunicadoBlockStylePatch(kpi, { boxShadow: undefined });
    expect(kpiNext.style?.boxShadow).toBeUndefined();
    expect(
      getKpiPartState(kpiNext.type === "kpi_view" ? kpiNext.kpiParts : null, { kind: "card" })?.style
        ?.boxShadow,
    ).toBe("none");
  });

  it("grava sombra na moldura de chart e filtro (não só block.style)", () => {
    const chart = createChartViewBlock("line");
    const chartNext = applyComunicadoBlockStylePatch(chart, {
      boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
    });
    expect(
      getChartPartState(chartNext.type === "chart_view" ? chartNext.chartParts : null, {
        kind: "chartArea",
      })?.style?.boxShadow,
    ).toBe("0 2px 8px rgba(0,0,0,0.2)");

    const input = createInputBlock();
    const inputCleared = applyComunicadoBlockStylePatch(input, { boxShadow: undefined });
    expect(
      getInputPartState(inputCleared.type === "input" ? inputCleared.inputParts : null, {
        kind: "frame",
      })?.style?.boxShadow,
    ).toBe("none");
  });

  it("mantém outras chaves ao limpar só a sombra", () => {
    const block = {
      ...createShapeBlock("rectangle"),
      style: { zIndex: 3, opacity: 0.8, boxShadow: "0 2px 10px rgba(0, 0, 0, 0.55)" },
    };
    const next = applyComunicadoBlockStylePatch(block, { boxShadow: undefined });
    expect(next.style?.boxShadow).toBeUndefined();
    expect(next.style?.zIndex).toBe(3);
    expect(next.style?.opacity).toBe(0.8);
  });

  it("tipografia do container remove override pontual nos contentRuns", () => {
    const block = {
      ...createShapeBlock("rectangle"),
      content: "Meta 1.400",
      contentRuns: [
        { text: "Meta ", style: { fontWeight: "bold" as const } },
        { text: "1.400", dataRef: { field: "ppm" }, style: { fontWeight: "normal" as const } },
      ],
      style: { zIndex: 2, fontWeight: "normal" as const },
    };
    const next = applyComunicadoBlockStylePatch(block, { fontWeight: "bold" });
    expect(next.style?.fontWeight).toBe("bold");
    expect(next.type).toBe("shape");
    if (next.type !== "shape") return;
    expect(next.contentRuns?.every((run) => run.style?.fontWeight == null)).toBe(true);
    expect(next.contentRuns?.some((run) => run.dataRef?.field === "ppm")).toBe(true);
  });
});
