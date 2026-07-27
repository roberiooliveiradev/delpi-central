import { MoveHorizontal, MoveVertical } from "lucide-react";
import { describe, expect, it } from "vitest";

import { resolveChartAddElementMenuRoots } from "./chartAddElementMenuCatalog";

describe("resolveChartAddElementMenuRoots", () => {
  it("ordem PPT-ish e choices reais (sem stubs Office)", () => {
    const roots = resolveChartAddElementMenuRoots("line");
    expect(roots.map((r) => r.elementId)).toEqual([
      "axes",
      "axisTitles",
      "chartTitle",
      "dataLabels",
      "dataTable",
      "gridlines",
      "legend",
      "markers",
    ]);
    const allIds = roots.flatMap((r) => r.choices.map((c) => c.id));
    expect(allIds).toContain("legend:left");
    expect(allIds).toContain("dataLabels:categoryPercent");
    expect(allIds).toContain("dataLabels:outsideEnd");
    expect(allIds).not.toContain("trendline");
    expect(allIds).not.toContain("errorBars");
  });

  it("ícones de Horizontal/Vertical alinham com o eixo (não seta/align)", () => {
    const axes = resolveChartAddElementMenuRoots("line").find((r) => r.elementId === "axes");
    expect(axes?.choices.find((c) => c.id === "axes:x")?.icon).toBe(MoveHorizontal);
    expect(axes?.choices.find((c) => c.id === "axes:y")?.icon).toBe(MoveVertical);
    const grid = resolveChartAddElementMenuRoots("line").find((r) => r.elementId === "gridlines");
    expect(grid?.choices.find((c) => c.id === "grid:horizontal")?.icon).toBe(MoveHorizontal);
    expect(grid?.choices.find((c) => c.id === "grid:vertical")?.icon).toBe(MoveVertical);
  });

  it("filtra marcadores fora de line/area", () => {
    expect(resolveChartAddElementMenuRoots("bar").some((r) => r.elementId === "markers")).toBe(
      false,
    );
  });
});
