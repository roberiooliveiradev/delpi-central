import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Top bar do deck: sem minimizar; sem seleção → aba Inserir (não Camadas).
 * Sem aba Página Inicial — hub fica na lista /apps/tv-dashboard.
 */
describe("deck chrome tab fallback contract", () => {
  const here = dirname(fileURLToPath(import.meta.url));
  const chrome = readFileSync(join(here, "DeckEditorChrome.tsx"), "utf8");
  const tabsMeta = readFileSync(join(here, "deck/deckRibbonTabMeta.ts"), "utf8");
  const selectionSrc = readFileSync(
    join(here, "../hooks/comunicadoEditor/useComunicadoEditorSelection.ts"),
    "utf8",
  );

  it("não expõe recolher/expandir da barra superior", () => {
    expect(chrome).not.toMatch(/chromeCollapsed/);
    expect(chrome).not.toMatch(/Recolher barra superior/);
    expect(chrome).not.toMatch(/td-deck-chrome--collapsed/);
    expect(chrome).not.toMatch(/ChevronUp/);
  });

  it("fallback sem aba válida / Camadas usa Inserir", () => {
    expect(chrome).toMatch(/resolveDefaultRibbonTab/);
    expect(chrome).toMatch(
      /Aba sumiu \(ex\.: limpou seleção\) → Inserir/,
    );
    expect(chrome).toMatch(
      /!tabs\.some\(\(tab\) => tab\.id === activeTab\) \|\| activeTab === "layers"/,
    );
  });

  it("abre slide custom na aba Inserir; sem home no chrome", () => {
    expect(chrome).toMatch(/isCustomSlide \? "insert" : "playlist"/);
    expect(chrome).not.toMatch(/activeTab === "home"/);
    expect(tabsMeta).not.toMatch(/id: "home"/);
  });

  it("Programação e Tela recebem chrome da antiga Página Inicial", () => {
    expect(chrome).toMatch(/DeckHomePlaylistChrome/);
    expect(chrome).toMatch(/SlideCurrentRibbon/);
  });

  it("Camadas não força aba da top bar (não colapsa o ribbon)", () => {
    expect(chrome).toMatch(/Painel Camadas ≠ aba da top bar/);
    expect(chrome).toMatch(/activeTab === "layers"/);
    expect(selectionSrc).not.toMatch(/setRibbonTabRequest\("layers"\)/);
  });
});
