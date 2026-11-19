import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const cssPath = join(
  dirname(fileURLToPath(import.meta.url)),
  "token-highlight-field.css",
);
const css = readFileSync(cssPath, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

const GEOMETRY_PROPS = [
  "padding",
  "margin",
  "width",
  "height",
  "min-width",
  "min-height",
  "max-width",
  "max-height",
  "top",
  "right",
  "bottom",
  "left",
  "inset",
  "gap",
  "border-width",
  "border-radius",
  "box-sizing",
  "position",
  "display",
  "font-size",
  "line-height",
  "letter-spacing",
  "white-space",
  "transform",
  "outline",
  "box-shadow",
  "overflow",
  "flex",
  "grid",
];

function darkBlocks(source: string): string[] {
  const blocks: string[] = [];
  const pattern =
    /:root\[data-theme="dark"\][^{]*,?\s*(?:\.theme-dark[^{]*)?\{([^}]*)\}/g;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(source)) !== null) {
    blocks.push(match[1]);
  }
  return blocks;
}

describe("token-highlight-field.css — contrato", () => {
  it("define os tokens de destaque nos dois temas", () => {
    expect(css).toMatch(/\.delpi-ui-token-highlight-field\s*\{[^}]*--delpi-ui-token-highlight-bg/s);
    expect(css).toMatch(/\.delpi-ui-token-highlight-field\s*\{[^}]*--delpi-ui-token-highlight-border/s);
    const dark = darkBlocks(css).join("\n");
    expect(dark).toMatch(/--delpi-ui-token-highlight-bg/);
    expect(dark).toMatch(/--delpi-ui-token-highlight-border/);
  });

  it("bloco do tema escuro não declara geometria", () => {
    for (const block of darkBlocks(css)) {
      for (const prop of GEOMETRY_PROPS) {
        expect(block).not.toMatch(new RegExp(`(?:^|[;{])\\s*${prop}\\s*:`, "m"));
      }
    }
  });

  it("sem seletor global e sem !important", () => {
    expect(css).not.toMatch(/!important/);
    expect(css).not.toMatch(/(^|\n)\s*\*\s*\{/);
    expect(css).not.toMatch(/(^|\n)\s*(html|body)\s*[{,]/);
  });

  it("camada não captura ponteiro e controle fica por cima", () => {
    expect(css).toMatch(
      /\.delpi-ui-token-highlight-field__backdrop\s*\{[^}]*pointer-events:\s*none/s,
    );
    expect(css).toMatch(
      /input\.delpi-ui-native-control\.delpi-ui-token-highlight-field__control,\s*\ntextarea\.delpi-ui-native-control\.delpi-ui-token-highlight-field__control\s*\{[^}]*position:\s*relative/s,
    );
    expect(css).toMatch(/background-color:\s*transparent/);
  });

  it("backdrop desenha fundo desabilitado igual ao controle nativo", () => {
    expect(css).toMatch(
      /__stack\[data-disabled\]\s+\.delpi-ui-token-highlight-field__backdrop\s*\{[^}]*88%/s,
    );
    expect(css).toMatch(
      /__stack\[data-readonly\]\s+\.delpi-ui-token-highlight-field__backdrop\s*\{[^}]*92%/s,
    );
  });

  it("quebra igual ao controle: pre-wrap multiline e pre na linha única", () => {
    expect(css).toMatch(
      /__stack\[data-multiline\]\s+\.delpi-ui-token-highlight-field__mirror\s*\{[^}]*white-space:\s*pre-wrap/s,
    );
    expect(css).toMatch(
      /\.delpi-ui-token-highlight-field__mirror\s*\{[^}]*white-space:\s*pre\b/s,
    );
  });

  it("forced-colors usa outline no lugar de fundo", () => {
    expect(css).toMatch(
      /@media\s*\(forced-colors:\s*active\)\s*\{[^}]*outline:/s,
    );
  });
});
