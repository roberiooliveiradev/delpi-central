import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const base = dirname(fileURLToPath(import.meta.url));

describe("DynamicContentInsertControl (contrato)", () => {
  const control = readFileSync(join(base, "DynamicContentInsertControl.tsx"), "utf8");
  const picker = readFileSync(join(base, "DynamicContentPickerPopover.tsx"), "utf8");
  const typography = readFileSync(join(base, "formatRibbon/FormatRibbonTypographySections.tsx"), "utf8");
  const grade = readFileSync(join(base, "CanvasTableDataBindingInspector.tsx"), "utf8");
  const shape = readFileSync(join(base, "ComunicadoEditorShapeBlock.tsx"), "utf8");
  const bridge = readFileSync(join(base, "../hooks/useVisualBoxTextEditorBridge.ts"), "utf8");

  it("ribbon e Grade usam o controle `{ }` com picker", () => {
    expect(typography).toContain("DynamicContentInsertControl");
    expect(typography).not.toContain("insertDataFieldAtCursor()");
    expect(grade).toContain("DynamicContentInsertControl");
    expect(control).toContain("applyDynamicContentSpec");
    expect(picker).toContain("DYNAMIC_CONTENT_KIND_CATALOG");
    expect(picker).toContain("data_field");
  });

  it("texto e forma registram insertDataRefAtSelection no bridge", () => {
    expect(bridge).toContain("insertDataRefAtSelection");
    expect(shape).toContain("insertDataRefAtSelection");
  });
});
