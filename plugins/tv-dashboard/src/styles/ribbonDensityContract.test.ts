import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Contrato de densidade do ribbon:
 * - band = altura fixa (Inserir/Home)
 * - fit = altura pelo conteúdo (Elemento/Dados) sem cortar
 * - grupos sem space-between (sem vazio até a caption)
 */
describe("ribbon density contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const css = readFileSync(join(base, "../index.css"), "utf8");
  const tileSource = readFileSync(join(base, "../components/deck/DeckRibbonTile.tsx"), "utf8");
  const shellSource = readFileSync(
    join(base, "../components/deck/DeckRibbonShell.tsx"),
    "utf8",
  );

  it("shell expõe densidades band e fit", () => {
    expect(shellSource).toMatch(/density\?: "band" \| "fit"/);
    expect(css).toMatch(/\.td-deck-ribbon--band/);
    expect(css).toMatch(/\.td-deck-ribbon--fit/);
  });

  it("band tem altura fixa; fit cresce até o teto sem clip rígido de 88px", () => {
    const band = css.match(
      /\.td-deck-ribbon--compact\.td-deck-ribbon--band\s*\{[^}]+\}/s,
    )?.[0];
    expect(band).toMatch(/--td-ribbon-height:\s*80px/);
    expect(band).toMatch(/height:\s*var\(--td-ribbon-height\)/);

    const fit = css.match(
      /\.td-deck-ribbon--compact\.td-deck-ribbon--fit\s*\{[^}]+\}/s,
    )?.[0];
    expect(fit).toMatch(/height:\s*auto/);
    expect(fit).toMatch(/max-height:\s*120px/);
  });

  it("tiles compactos usam ícone Lucide 18 e faixa de uma linha", () => {
    expect(tileSource).toMatch(/Icon size=\{18\}/);
    expect(css).toMatch(
      /\.td-deck-ribbon--compact \.td-ribbon-tile__icon\s*\{[^}]*width:\s*22px/s,
    );
    expect(css).toMatch(
      /\.td-deck-ribbon--compact \.td-deck-ribbon__tiles\s*\{[^}]*grid-template-rows:\s*auto/s,
    );
  });

  it("grupos compactos não usam space-between (evita vazio vertical)", () => {
    const group = css.match(
      /\.td-deck-ribbon--compact \.td-deck-ribbon__group\s*\{[^}]+\}/s,
    )?.[0];
    expect(group).toMatch(/justify-content:\s*flex-start/);
    expect(group).not.toMatch(/justify-content:\s*space-between/);
  });

  it("inputs de frame têm largura legível (≥72px)", () => {
    expect(css).toMatch(
      /\.td-deck-ribbon--compact \.td-deck-ribbon__frame-grid\s*\{[^}]*minmax\(76px/s,
    );
    expect(css).toMatch(
      /\.td-deck-ribbon--compact \.td-deck-ribbon__number--compact\s*\{[^}]*width:\s*72px/s,
    );
  });

  it("group--wide compacto não estica com flex:1", () => {
    const block = css.match(
      /\.td-deck-ribbon--compact \.td-deck-ribbon__group--wide\s*\{[^}]+\}/s,
    )?.[0];
    expect(block).toBeTruthy();
    expect(block).toMatch(/flex:\s*0\s+0\s+auto/);
  });
});
