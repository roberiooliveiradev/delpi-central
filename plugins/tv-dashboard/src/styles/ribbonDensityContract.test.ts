import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Contrato de densidade do ribbon (--compact): tiles legíveis, grupos hug, painéis sem 1fr vazio.
 */
describe("ribbon density contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const css = readFileSync(join(base, "../index.css"), "utf8");
  const tileSource = readFileSync(join(base, "../components/deck/DeckRibbonTile.tsx"), "utf8");

  it("tiles compactos usam ícone Lucide 18 e caixa ≥22px", () => {
    expect(tileSource).toMatch(/Icon size=\{18\}/);
    expect(css).toMatch(
      /\.td-deck-ribbon--compact \.td-ribbon-tile__icon\s*\{[^}]*width:\s*22px/s,
    );
    expect(css).toMatch(
      /\.td-deck-ribbon--compact \.td-ribbon-tile\s*\{[^}]*min-width:\s*48px/s,
    );
  });

  it("group--wide compacto não estica com flex:1", () => {
    const block = css.match(
      /\.td-deck-ribbon--compact \.td-deck-ribbon__group--wide\s*\{[^}]+\}/s,
    )?.[0];
    expect(block).toBeTruthy();
    expect(block).toMatch(/flex:\s*0\s+0\s+auto/);
    expect(block).not.toMatch(/flex:\s*1\s+1\s+auto/);
  });

  it("painéis Dados/Camadas limitam colunas (sem 1fr full-bleed)", () => {
    expect(css).toMatch(
      /\.td-deck-ribbon__panel--layers\s*\{[^}]*minmax\(280px,\s*420px\)/s,
    );
    expect(css).toMatch(/\.td-deck-ribbon__panel--dados\s*\{[^}]*minmax\(200px,\s*280px\)/s);
  });
});
