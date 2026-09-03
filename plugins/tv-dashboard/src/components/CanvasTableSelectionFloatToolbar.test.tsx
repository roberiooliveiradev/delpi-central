import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("CanvasTableSelectionFloatToolbar chrome", () => {
  const source = readFileSync(join(here, "CanvasTableSelectionFloatToolbar.tsx"), "utf8");

  it("usa menus chart/table e remove FloatChecklist legado", () => {
    expect(source).toContain("CanvasTableStructureMenu");
    expect(source).toContain("CanvasTableBlockStylesMenu");
    expect(source).toContain("CanvasTableCellFormatMenu");
    expect(source).toContain("CanvasTableDataMenu");
    expect(source).toContain("ComplexSelectionFloatToolbar");
    expect(source).not.toContain("FloatChecklist");
    expect(source).not.toContain("td-deck-ribbon__float-panel");
  });

  it("alterna CellFormatMenu com célula e BlockStylesMenu sem seleção", () => {
    expect(source).toContain("hasCellSelection");
    expect(source).toMatch(/hasCellSelection[\s\S]*CanvasTableCellFormatMenu/);
    expect(source).toMatch(/CanvasTableBlockStylesMenu/);
  });
});
