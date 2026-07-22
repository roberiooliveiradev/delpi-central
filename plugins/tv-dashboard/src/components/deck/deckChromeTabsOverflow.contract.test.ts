import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

describe("deck chrome tabs overflow contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const chrome = readFileSync(join(base, "../DeckEditorChrome.tsx"), "utf8");
  const embedded = readFileSync(join(base, "../ComunicadoEmbeddedEditorChrome.tsx"), "utf8");
  const css = readFileSync(join(base, "../../index.css"), "utf8");
  const row = readFileSync(join(base, "DeckChromeTabsRow.tsx"), "utf8");

  it("chromes usam DeckChromeTabsRow (sem scroll horizontal de abas)", () => {
    expect(chrome).toContain("DeckChromeTabsRow");
    expect(embedded).toContain("DeckChromeTabsRow");
    expect(chrome).not.toMatch(/overflow-x:\s*auto/);
    expect(row).toContain("resolveOverflowRibbonTabIds");
    expect(row).toContain("Mais");
  });

  it("CSS das tabs não usa overflow-x auto; histórico fica fora da faixa medida", () => {
    expect(css).toMatch(
      /\.td-deck-chrome__tabs\s*\{[^}]*overflow:\s*hidden/s,
    );
    expect(css).not.toMatch(
      /\.td-deck-chrome__tabs\s*\{[^}]*overflow-x:\s*auto/s,
    );
    expect(css).not.toContain("left: -9999px");
    expect(css).toMatch(
      /\.td-deck-chrome__tabs-measure\s*\{[^}]*position:\s*fixed/s,
    );
    expect(css).toContain("td-deck-chrome__tabs-measure-inner");
    expect(css).toContain("td-deck-chrome__tabs-more-portal");
    expect(chrome).toMatch(
      /DeckHistoryTabActions[\s\S]*DeckChromeTabsRow/s,
    );
  });
});
