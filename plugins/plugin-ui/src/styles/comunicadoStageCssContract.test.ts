import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Contrato do palco comunicado no kit — overflow clip + tipografia sem flex:1.
 */
describe("comunicado-stage.css contract (plugin-ui)", () => {
  const css = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "comunicado-stage.css"),
    "utf8",
  );

  it("moldura de design com overflow visible + tipografia de design (WYSIWYG)", () => {
    expect(css).toMatch(/\.tdp-native-screen\.delpi-ui-comunicado\s*\{[^}]*display:\s*block/s);
    const root = css.match(/(?:^|[\s,}])\.delpi-ui-comunicado\s*\{([\s\S]*?)\}/m);
    expect(root?.[1] ?? "").toMatch(/overflow:\s*visible/);
    expect(root?.[1] ?? "").toMatch(/font-size:\s*16px/);
    expect(root?.[1] ?? "").toMatch(/width:\s*100%/);
    expect(root?.[1] ?? "").toMatch(/height:\s*100%/);
    expect(css).toMatch(
      /\.delpi-ui-comunicado__background\s*\{[^}]*object-fit:\s*cover[^}]*object-position:\s*center/s,
    );
    expect(css).toMatch(/\.delpi-ui-comunicado__stage\s*\{[^}]*position:\s*absolute[^}]*inset:\s*0/s);
    expect(css).toMatch(/\.tdp-stage--animate-entrances/);
  });

  it("tipografia da caixa visual sem padding no wrapper nem flex:1", () => {
    const baseBlock = css.match(/\.delpi-ui-comunicado__block\s*\{([\s\S]*?)\}/);
    expect(baseBlock?.[1] ?? "").toMatch(/padding:\s*0\s*;/);
    expect(baseBlock?.[1] ?? "").not.toMatch(/padding:\s*0\.4em/);
    expect(css).toMatch(/flex:\s*0\s+0\s+auto/);
    expect(css).toMatch(/\.delpi-ui-comunicado__shape-text\s*\{[^}]*pointer-events:\s*none/s);
  });

  it("formas SVG de área usam non-scaling-stroke (paridade com border CSS do retângulo)", () => {
    expect(css).toMatch(/vector-effect:\s*non-scaling-stroke/);
    expect(css).toMatch(/stroke-linejoin:\s*round/);
  });

  it("editor libera overflow do bloco Grade (handles/gutter); TV/prévia mantém clip", () => {
    expect(css).toMatch(
      /\.delpi-ui-comunicado--editor\s+\.delpi-ui-comunicado__block--canvas_table[\s\S]*?overflow:\s*visible/,
    );
    const tvBlock = css.match(
      /\.delpi-ui-comunicado__block--canvas_table,\s*\n\.delpi-ui-comunicado__block--canvas-table\s*\{([\s\S]*?)\}/,
    );
    expect(tvBlock?.[1] ?? "").toMatch(/overflow:\s*hidden/);
  });

  it("Grade td/th não força pre-wrap; rich text herda wrap da célula", () => {
    const tdRule = css.match(/\.td-canvas-table th,\s*\n\.td-canvas-table td\s*\{([\s\S]*?)\}/);
    expect(tdRule?.[1] ?? "").not.toMatch(/white-space:\s*pre-wrap/);
    expect(css).toMatch(
      /\.td-canvas-table\s+\.delpi-ui-comunicado__rich-text[\s\S]*?white-space:\s*inherit/,
    );
  });

  it("alça AutoFill só no editor editable + cursor crosshair", () => {
    expect(css).toContain(".td-canvas-table__fill-handle");
    expect(css).toContain(".td-canvas-table__fill-preview");
    expect(css).toMatch(
      /\.td-canvas-table--editable\s+\.td-canvas-table__fill-handle[\s\S]*?display:\s*block/,
    );
    expect(css).toMatch(/\.td-canvas-table__fill-handle[\s\S]*?cursor:\s*crosshair/);
  });

  it("marcadores de lista compartilham chrome leitura (ul/ol) e edição (data-list-type)", () => {
    expect(css).toMatch(/\.delpi-ui-comunicado__list\s*\{[^}]*list-style:\s*none/);
    expect(css).not.toMatch(/\.delpi-ui-comunicado__list--bullet\s*\{[^}]*list-style-type:\s*disc/);
    expect(css).toMatch(
      /\.delpi-ui-comunicado__list--bullet > \.delpi-ui-comunicado__list-item::before[\s\S]*?border-radius:\s*50%/,
    );
    expect(css).toMatch(
      /\.delpi-ui-comunicado__rich-text \[data-comunicado-line\]\[data-list-type="bullet"\]::before[\s\S]*?border-radius:\s*50%/,
    );
    expect(css).toMatch(
      /\.delpi-ui-comunicado__rich-text \[data-comunicado-line\]\[data-list-type="ordered"\]::before[\s\S]*?counter\(delpi-comunicado-ol\)/,
    );
  });
});
