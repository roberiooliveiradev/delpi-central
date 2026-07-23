import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Grade (canvas_table) — topbar/sidebar no padrão Tabela/KPI:
 * tiles Lucide + controles canônicos do plugin-ui (sem checkbox/select nativo solto).
 */
describe("CanvasTableSection chrome (plugin-ui + ícones)", () => {
  const source = readFileSync(resolve(__dirname, "./CanvasTableSection.tsx"), "utf8");
  const collapseIcons = readFileSync(
    resolve(__dirname, "../deck/deckRibbonCollapseIcons.ts"),
    "utf8",
  );

  it("usa tiles Lucide e controles plugin-ui", () => {
    expect(source).toContain("DeckRibbonTile");
    expect(source).toContain("ComboboxNumberControl");
    expect(source).toContain("ToolbarSelectField");
    expect(source).toContain("TvRibbonColorPicker");
    expect(source).toContain("TdRibbonSelect");
    expect(source).toContain("Heading2");
    expect(source).toContain("Grid3x3");
    expect(source).toContain("AlignLeft");
  });

  it("não reintroduz NativeCheckbox/NativeSelect no inspetor Grade", () => {
    expect(source).not.toContain("NativeCheckboxControl");
    expect(source).not.toContain("NativeSelectControl");
  });

  it("groupIds de collapse cobrem Grade / Estilo / Célula", () => {
    expect(collapseIcons).toContain('"canvas-table"');
    expect(collapseIcons).toContain('"canvas-table-design"');
    expect(collapseIcons).toContain('"canvas-table-cell"');
  });
});
