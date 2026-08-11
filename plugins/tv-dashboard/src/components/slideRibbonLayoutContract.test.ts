import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

/**
 * Aba Tela deve seguir o molde Inserir: tiles ícone+rótulo; formulários em popover
 * (sem prop-cols / chips / pills vazando na band de 112px).
 */
describe("slide ribbon layout contract", () => {
  it("Propriedades usam tiles + popover, não formulário inline na band", () => {
    const panel = readFileSync(join(here, "DeckSettingsPanel.tsx"), "utf8");
    expect(panel).toContain("DeckRibbonTilePopover");
    expect(panel).toContain('label="Título"');
    expect(panel).toContain('label="Duração"');
    expect(panel).toContain('label="Transição"');
    expect(panel).toContain("Herdar duração");
    expect(panel).toContain("buildSparseSlidePatch");
    expect(panel).toContain("onSaveSlides");
    expect(panel).toContain("titleMixed");
    expect(panel).not.toContain("td-deck-ribbon__prop-cols");
    expect(panel).not.toContain("td-deck-settings-chip");
  });

  it("Ferramentas e Tipo usam DeckRibbonTile", () => {
    const accordion = readFileSync(join(here, "deck/DeckSettingsAccordion.tsx"), "utf8");
    const background = readFileSync(join(here, "deck/ComunicadoSlideBackgroundRibbon.tsx"), "utf8");
    expect(accordion).toContain("DeckRibbonTile");
    expect(accordion).not.toContain("td-deck-settings-accordion__summary");
    expect(background).toContain('label="Início"');
    expect(background).toContain('label="Fim"');
    expect(background).toContain("td-deck-ribbon__tiles");
  });

  it("popovers da aba Tela usam chrome canônico do kit", () => {
    const accordion = readFileSync(join(here, "deck/DeckSettingsAccordion.tsx"), "utf8");
    const tilePopover = readFileSync(join(here, "deck/DeckRibbonTilePopover.tsx"), "utf8");
    const css = readFileSync(join(here, "../index.css"), "utf8");
    expect(accordion).toContain("delpi-ui-popover-surface");
    expect(tilePopover).toContain("delpi-ui-popover-surface");
    expect(css).toMatch(
      /\.td-deck-settings-accordion__body\{[^}]*max-height:\s*min\(520px,\s*72vh\)/s,
    );
    expect(css).not.toMatch(
      /\.td-deck-settings-accordion__body\{[^}]*max-height:\s*min\(240px/s,
    );
    expect(css).not.toMatch(
      /\.td-deck-settings-accordion__body\{[^}]*box-shadow:\s*0 8px 24px/s,
    );
  });
});
