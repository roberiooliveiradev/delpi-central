import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("VisualDataViewInspector column toggle", () => {
  it("reconcilia partes por chave (fluxo central) em vez de clear pontual", () => {
    const source = readFileSync(resolve(__dirname, "./VisualDataViewInspector.tsx"), "utf8");
    const apply = source.slice(
      source.indexOf("const applyTableProjection"),
      source.indexOf("const applyKpiProjection"),
    );
    expect(apply).toContain("reconcileTablePartsForVisibleKeys");
    expect(apply).not.toContain("clearTablePartSelection");
    expect(apply).not.toMatch(/selectTablePart\s*\(/);

    const chartApply = source.slice(
      source.indexOf("const applyChartProjection"),
      source.indexOf("const connectionBody"),
    );
    expect(chartApply).toContain("reconcileChartPartForSeriesFields");
  });
});
