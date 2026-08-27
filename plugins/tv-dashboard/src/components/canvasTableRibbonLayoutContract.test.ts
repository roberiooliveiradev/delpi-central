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
});
