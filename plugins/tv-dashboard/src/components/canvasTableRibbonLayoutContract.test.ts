import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

/** Grade — mesmo molde Tabela Layout: popover Estrutura na band. */
describe("canvas table ribbon layout contract", () => {
  it("Grade usa DeckRibbonTilePopover Estrutura e não frame-grid solto na band", () => {
    const source = readFileSync(join(here, "selectionSections/CanvasTableSection.tsx"), "utf8");
    expect(source).toContain("DeckRibbonTilePopover");
    expect(source).toContain('label="Estrutura"');
    expect(source).toContain("structureFields");
    expect(source).not.toContain("DeckRibbonLargeButton");
    expect(source).toMatch(/layout === "ribbon"[\s\S]*DeckRibbonTilePopover[\s\S]*structureFields/);
  });

  it("ribbon Célula compacta com tiles, popover Tipo e multi-seleção", () => {
    const source = readFileSync(join(here, "selectionSections/CanvasTableSection.tsx"), "utf8");
    expect(source).toContain("td-canvas-table-cell-ribbon");
    expect(source).toContain('label="Tipo"');
    expect(source).toContain('label="Formato"');
    expect(source).toContain("CanvasTableCellFormatMenu");
    expect(source).toContain("summarizeCanvasTableCellSelection");
    expect(source).toContain("patchCanvasTableCellsStyle");
    expect(source).not.toMatch(/function patchSelectedCellsStyle/);
    expect(source).not.toContain("Fonte (px)");
    expect(source).not.toMatch(/label="Esquerda"/);
    expect(source).not.toMatch(/label="Centro"/);
    expect(source).not.toMatch(/label="Direita"/);
  });

  it("seleção da Grade usa overlay CSS — sem outline no td --selected", () => {
    const css = readFileSync(
      join(here, "../../../plugin-ui/src/styles/comunicado-stage.css"),
      "utf8",
    );
    expect(css).toContain(".td-canvas-table__sel-range");
    expect(css).toContain(".td-canvas-table__sel-focus");
    expect(css).toContain(".td-canvas-table__col-handle");
    expect(css).toContain(".td-canvas-table__row-handle");
    expect(css).toContain(".td-canvas-table--editable .td-canvas-table__col-handle");
    expect(css).not.toMatch(
      /\.td-canvas-table--editable\s*\{[^}]*padding/,
    );
    expect(css).not.toMatch(/\.td-canvas-table__cell--selected\s*\{[^}]*outline/);
    expect(css).toMatch(
      /\.td-canvas-table\s*\{[^}]*position:\s*relative/,
    );
  });
});
