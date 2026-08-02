import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

/**
 * Aba Programação — mesmo molde da aba Tela: tiles + popover (sem formulário
 * inline vazando na band de 112px).
 */
describe("playlist ribbon layout contract", () => {
  it("Rotação / Link / Master usam DeckRibbonTilePopover", () => {
    const panel = readFileSync(join(here, "DeckSettingsPanel.tsx"), "utf8");
    expect(panel).toContain('groupId="playlist-rotation"');
    expect(panel).toContain('label="Resolução"');
    expect(panel).toContain('label="Duração"');
    expect(panel).toContain('label="Atualizar"');
    expect(panel).toContain("DeckRibbonTilePopover");
    expect(panel).toContain('groupId="playlist-link"');
    expect(panel).toContain('groupId="playlist-master"');
    expect(panel).not.toContain("td-deck-tabs__grid--playlist-rotation");
    expect(panel).not.toContain("td-deck-playlist-link");
    expect(panel).not.toContain("td-deck-master--compact");
  });

  it("DeckRibbonTilePopover marca surface section-popover para nested (cores)", () => {
    const source = readFileSync(join(here, "deck/DeckRibbonTilePopover.tsx"), "utf8");
    expect(source).toContain("RibbonGroupSurfaceProvider");
    expect(source).toContain('value="section-popover"');
  });
});
