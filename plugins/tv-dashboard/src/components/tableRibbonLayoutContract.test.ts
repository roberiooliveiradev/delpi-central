import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

/**
 * Abas Design da Tabela / Tabela Layout — mesmo molde Tela/Programação:
 * tiles + DeckRibbonTilePopover (formulários fora da band de 112px).
 */
describe("table ribbon layout contract", () => {
  it("Design usa DeckRibbonTilePopover e não LargeButton na band", () => {
    const design = readFileSync(join(here, "selectionSections/TableDesignSections.tsx"), "utf8");
    expect(design).toContain("DeckRibbonTilePopover");
    expect(design).toContain('label="Adicionar elemento"');
    expect(design).toContain('label="Alterar estilos"');
    expect(design).toContain('label="Selecionar dados"');
    expect(design).toContain('label="Caneta"');
    expect(design).toContain('label="Ajuste"');
    expect(design).not.toContain("DeckRibbonLargeButton");
    expect(design).not.toContain("AnchoredPanelPortal");
    /* Um tile só — wide forçava min-width ~240px e buraco na band. */
    expect(design).toMatch(
      /TableStyleOptionsBandOrInline[\s\S]*?false,\s*"table-style-options"/,
    );
  });

  it("Layout Tamanho usa tile Dimensões + popover, sem frame-grid na band", () => {
    const layout = readFileSync(join(here, "selectionSections/TableLayoutSections.tsx"), "utf8");
    expect(layout).toContain("DeckRibbonTilePopover");
    expect(layout).toContain('label="Dimensões"');
    expect(layout).toContain('groupId="table-layout-size"');
    /* Campos existem no popover; a band ribbon não deve montar frame-grid solto. */
    const ribbonReturn = layout.slice(layout.indexOf('groupId="table-layout-size"'));
    expect(ribbonReturn).toContain("DeckRibbonTilePopover");
    expect(ribbonReturn).toContain("{fields}");
  });
});
