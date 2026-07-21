import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Top bar do deck: sem minimizar; sem seleção → aba Inserir (não Camadas).
 */
describe("deck chrome tab fallback contract", () => {
  const chrome = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "DeckEditorChrome.tsx"),
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
    expect(chrome).toMatch(/\/\* Aba sumiu[\s\S]*resolveDefaultRibbonTab\(tabs, isCustomSlide\)/);
    expect(chrome).not.toMatch(/Aba sumiu[\s\S]*setActiveTab\("layers"\)/);
  });

  it("abre slide custom na aba Inserir", () => {
    expect(chrome).toMatch(/isCustomSlide \? "insert" : "home"/);
  });
});
