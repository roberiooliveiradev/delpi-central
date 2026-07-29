import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("VisualDataViewInspector column toggle", () => {
  it("não remapeia selectTablePart ao alterar projeção (evita esvaziar Design)", () => {
    const source = readFileSync(resolve(__dirname, "./VisualDataViewInspector.tsx"), "utf8");
    const apply = source.slice(
      source.indexOf("const applyTableProjection"),
      source.indexOf("const applyKpiProjection"),
    );
    expect(apply).toContain("clearTablePartSelection");
    expect(apply).not.toMatch(/selectTablePart\s*\(/);
  });
});
