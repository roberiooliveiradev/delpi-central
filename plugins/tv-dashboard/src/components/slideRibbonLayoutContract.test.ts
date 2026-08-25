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
    expect(background).toContain('label="Cor"');
    expect(background).toContain("onFillChange");
    expect(background).toContain("TV_ALLOWED_FILL_KINDS");
    expect(background).not.toContain('label="Início"');
    expect(background).not.toContain('label="Fim"');
    expect(background).not.toContain("slide-presets");
    expect(background).toContain("td-deck-ribbon__tiles");
    expect(background).toContain("selectedSlides");
    expect(background).toContain("backgroundSlides");
    expect(background).toContain("TV_DASHBOARD_HELP_TOOLTIPS.ribbon");
    expect(background).toMatch(/const H = TV_DASHBOARD_HELP_TOOLTIPS\.ribbon/);
    expect(background).not.toContain('label="Biblioteca"');
    expect(background).not.toContain("openMediaLibrary");
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

  it("fan-out de fundo/filtros fica na página, sem API no hook do editor", () => {
    const page = readFileSync(join(here, "../pages/PlaylistEditorPage.tsx"), "utf8");
    const hook = readFileSync(
      join(here, "../hooks/comunicadoEditor/useComunicadoEditorBlocks.ts"),
      "utf8",
    );
    expect(page).toContain("pickSharedCustomSlideConfig");
    expect(page).toContain("persistSharedCustomFanOut");
    expect(hook).not.toContain("updateSlide(");
    expect(hook).not.toContain("applySlideBatchPatch");
  });
});
