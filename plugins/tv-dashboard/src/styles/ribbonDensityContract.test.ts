import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Contrato de densidade do ribbon:
 * - band = altura fixa (todas as abas contextuais — evita reflow do palco)
 * - fit = altura pelo conteúdo (legado CSS; chrome atual usa band)
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
  const deckChrome = readFileSync(
    join(base, "../components/DeckEditorChrome.tsx"),
    "utf8",
  );

  it("shell expõe densidades band e fit", () => {
    expect(shellSource).toMatch(/density\?: "band" \| "fit"/);
    expect(css).toMatch(/\.td-deck-ribbon--band/);
    expect(css).toMatch(/\.td-deck-ribbon--fit/);
  });

  it("chrome contextual usa band para não alterar altura do palco", () => {
    expect(deckChrome).toMatch(/function ribbonDensityFor[\s\S]*return "band"/);
  });

  it("band tem altura fixa; fit cresce até o teto sem clip rígido de 88px", () => {
    const band = css.match(
      /\.td-deck-ribbon--compact\.td-deck-ribbon--band\s*\{[^}]+\}/s,
    )?.[0];
    expect(band).toMatch(/--td-ribbon-height:\s*112px/);
    expect(band).toMatch(/height:\s*var\(--td-ribbon-height\)/);

    const fit = css.match(
      /\.td-deck-ribbon--compact\.td-deck-ribbon--fit\s*\{[^}]+\}/s,
    )?.[0];
    expect(fit).toMatch(/height:\s*auto/);
    expect(fit).toMatch(/max-height:\s*min\(220px,\s*34vh\)/);
  });

  it("Raio/Opacidade na ribbon mantêm slider (full) com largura estreita no host", () => {
    const opacity = readFileSync(
      join(base, "../components/formatRibbon/FormatRibbonOrganizeSection.tsx"),
      "utf8",
    );
    const corner = readFileSync(
      join(base, "../components/ShapeCornerRadiusControl.tsx"),
      "utf8",
    );
    const hostDensity = readFileSync(
      join(base, "../../../plugin-ui/src/styles/host-density-compact.css"),
      "utf8",
    );
    expect(opacity).toMatch(/id="td-block-opacity"[\s\S]*density="full"/);
    expect(corner).toMatch(/label="Raio \(px\)"[\s\S]*density="full"/);
    expect(hostDensity).toMatch(
      /\[data-delpi-ui-density="compact"\]\s*\.delpi-ui-range-field\s*\{[^}]*width:\s*96px/s,
    );
  });

  it("tokens de densidade chrome PPT estão declarados", () => {
    expect(css).toMatch(/--td-chrome-radius:\s*2px/);
    expect(css).toMatch(/--td-ribbon-tile-radius:\s*4px/);
    expect(css).toMatch(/--td-ribbon-gallery-thumb:\s*44px/);
    expect(css).toMatch(/--td-chrome-tab-height:\s*36px/);
  });

  it("chrome usa scroll X no ribbon fit (faixa única) e clipa Y", () => {
    expect(css).toMatch(
      /\.td-deck-chrome__ribbon:has\(\.td-deck-ribbon--fit\)\s*\{[^}]*overflow-x:\s*auto/s,
    );
    expect(css).toMatch(
      /\.td-deck-chrome__ribbon \.td-deck-ribbon--fit\s*\{[^}]*overflow-y:\s*hidden/s,
    );
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
      /\.td-deck-ribbon--compact \.td-deck-ribbon__frame-grid\s*\{[^}]*flex-wrap:\s*nowrap/s,
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
