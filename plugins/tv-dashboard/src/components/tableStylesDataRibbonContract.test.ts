import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("table styles/data ribbon parity", () => {
  it("ribbon e float compartilham TableStylesMenu e TableDataMenu", () => {
    const sections = readFileSync(join(here, "selectionSections/TableDesignSections.tsx"), "utf8");
    const floatToolbar = readFileSync(join(here, "TableSelectionFloatToolbar.tsx"), "utf8");
    expect(sections).toContain("TableStylesMenu");
    expect(sections).toContain("TableDataMenu");
    expect(sections).toContain("Alterar\\nestilos");
    expect(sections).toContain("Selecionar\\ndados");
    expect(floatToolbar).toContain("TableStylesMenu");
    expect(floatToolbar).toContain("TableDataMenu");
    expect(floatToolbar).not.toContain("FloatChecklist");
  });
});
