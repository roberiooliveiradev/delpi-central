import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Contrato de densidade do ribbon (--compact): altura fixa, faixa horizontal, sem scroll vertical.
 */
describe("ribbon density contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const css = readFileSync(join(base, "../index.css"), "utf8");
  const tileSource = readFileSync(join(base, "../components/deck/DeckRibbonTile.tsx"), "utf8");

  it("ribbon compacta tem altura fixa padrão", () => {
    expect(css).toMatch(/--td-ribbon-height:\s*88px/);
    const compact = css.match(/\.td-deck-ribbon--compact\s*\{[^}]+\}/s)?.[0];
    expect(compact).toBeTruthy();
    expect(compact).toMatch(/height:\s*var\(--td-ribbon-height\)/);
    expect(compact).toMatch(/overflow:\s*hidden/);
  });

  it("tiles compactos usam ícone Lucide 18 e faixa de uma linha", () => {
    expect(tileSource).toMatch(/Icon size=\{18\}/);
    expect(css).toMatch(
      /\.td-deck-ribbon--compact \.td-ribbon-tile__icon\s*\{[^}]*width:\s*22px/s,
    );
    expect(css).toMatch(
      /\.td-deck-ribbon--compact \.td-ribbon-tile\s*\{[^}]*min-height:\s*52px/s,
    );
    expect(css).toMatch(
      /\.td-deck-ribbon--compact \.td-deck-ribbon__tiles\s*\{[^}]*grid-template-rows:\s*auto/s,
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

  it("painéis Dados/Camadas não usam scroll vertical", () => {
    expect(css).toMatch(
      /\.td-deck-ribbon__panel--layers\s*\{[^}]*minmax\(280px,\s*420px\)/s,
    );
    expect(css).toMatch(/\.td-deck-ribbon__panel--dados\s*\{[^}]*minmax\(200px,\s*280px\)/s);
    const panel = css.match(/\.td-deck-ribbon__panel\s*\{[^}]+\}/s)?.[0];
    expect(panel).toMatch(/overflow-y:\s*hidden/);
  });

  it("Organizar fica em linha (tiles + props) sem empilhar verticalmente", () => {
    const organize = css.match(/\.td-deck-ribbon__organize\s*\{[^}]+\}/s)?.[0];
    expect(organize).toMatch(/flex-direction:\s*row/);
  });
});
