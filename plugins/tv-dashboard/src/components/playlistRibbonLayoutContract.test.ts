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
  it("Rotação / Filtros / Link / Master usam DeckRibbonTilePopover", () => {
    const panel = readFileSync(join(here, "DeckSettingsPanel.tsx"), "utf8");
    expect(panel).toContain('groupId="playlist-rotation"');
    expect(panel).toContain('label="Resolução"');
    expect(panel).toContain("ViewportResolutionFields");
    expect(panel).toContain('label="Duração"');
    expect(panel).toContain('label="Atualizar"');
    expect(panel).toContain("DeckRibbonTilePopover");
    expect(panel).toContain('groupId="playlist-filters"');
    expect(panel).toContain("PlaylistDataFiltersFields");
    expect(panel).toContain('onSavePlaylistSettings("dataDefaults"');
    expect(panel).toContain('groupId="playlist-link"');
    expect(panel).toContain('groupId="playlist-master"');
    expect(panel).toContain('groupId="playlist-media"');
    expect(panel).toContain('label="Biblioteca"');
    expect(panel).toContain("openPlaylistMediaLibrary");
    expect(panel).toContain('label="Modo"');
    expect(panel).toContain('onSavePlaylistSettings("playbackMode"');
    expect(panel).not.toContain("td-deck-tabs__grid--playlist-rotation");
    expect(panel).not.toContain("td-deck-playlist-link");
    expect(panel).not.toContain("td-deck-master--compact");
  });

  it("ViewportResolutionFields expõe Personalizado + L/A + unidade", () => {
    const fields = readFileSync(join(here, "ViewportResolutionFields.tsx"), "utf8");
    expect(fields).toContain("listViewportProfileSelectOptions");
    expect(fields).toContain('label="Unidade"');
    expect(fields).toContain("VIEWPORT_LENGTH_UNITS");
    expect(fields).toContain('aria-label="Largura da resolução"');
    expect(fields).toContain('aria-label="Altura da resolução"');
    expect(fields).toContain('viewportProfile: "custom"');
  });

  it("popover de Resolução não força scroll em formulário curto", () => {
    const panel = readFileSync(join(here, "DeckSettingsPanel.tsx"), "utf8");
    expect(panel).toContain("td-deck-ribbon-tile-popover--viewport");
    const css = readFileSync(join(here, "../index.css"), "utf8");
    expect(css).toMatch(
      /\.td-deck-ribbon-tile-popover--viewport\s*\{[^}]*max-height:\s*none/s,
    );
    expect(css).toMatch(
      /\.td-deck-ribbon-tile-popover--viewport\s*\{[^}]*overflow:\s*visible/s,
    );
  });

  it("ícone de colapso playlist-filters registrado", () => {
    const icons = readFileSync(join(here, "deck/deckRibbonCollapseIcons.ts"), "utf8");
    expect(icons).toContain('"playlist-filters"');
  });

  it("DeckRibbonTilePopover marca surface section-popover para nested (cores)", () => {
    const source = readFileSync(join(here, "deck/DeckRibbonTilePopover.tsx"), "utf8");
    expect(source).toContain("RibbonGroupSurfaceProvider");
    expect(source).toContain('value="section-popover"');
  });
});
