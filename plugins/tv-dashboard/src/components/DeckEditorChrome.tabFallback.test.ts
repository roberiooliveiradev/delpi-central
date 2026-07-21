import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Top bar do deck: sem minimizar; sem seleção → aba Inserir (não Camadas).
 * Sem aba Página Inicial — hub fica na lista /apps/tv-dashboard.
 */
describe("deck chrome tab fallback contract", () => {
  const chrome = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "DeckEditorChrome.tsx"),
    "utf8",
  );
  const tabsMeta = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "deck/deckRibbonTabMeta.ts"),
    "utf8",
  );

  it("não expõe recolher/expandir da barra superior", () => {
    expect(chrome).not.toMatch(/chromeCollapsed/);
    expect(chrome).not.toMatch(/Recolher barra superior/);
    expect(chrome).not.toMatch(/td-deck-chrome--collapsed/);
    expect(chrome).not.toMatch(/ChevronUp/);
  });

  it("fallback sem aba válida / sem seleção usa Inserir", () => {
    expect(chrome).toMatch(/resolveDefaultRibbonTab/);
    expect(chrome).toMatch(
      /Aba sumiu \(ex\.: limpou seleção\) → Inserir/,
    );
    expect(chrome).toMatch(
      /if \(!tabs\.some\(\(tab\) => tab\.id === activeTab\)\) \{\s*setActiveTab\(resolveDefaultRibbonTab/,
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
});
