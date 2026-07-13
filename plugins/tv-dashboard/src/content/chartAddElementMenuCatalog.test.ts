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
    expect(allIds).not.toContain("trendline");
    expect(allIds).not.toContain("errorBars");
  });

  it("filtra marcadores fora de line/area", () => {
    expect(resolveChartAddElementMenuRoots("bar").some((r) => r.elementId === "markers")).toBe(
      false,
    );
  });
});
