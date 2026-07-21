import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Contrato: tipografia em caixa visual alinhada ao editor.
 * Causa raiz da divergência editor×TV / preview:
 * - padding no wrapper `.tdp-comunicado__block` (TV encolhia; editor tinha 0)
 * - flex:1 em h1/p (anulava verticalAlign e cortava texto)
 * - justify/padding hardcoded em `.tdp-comunicado__shape-text`
 */
describe("visual box typography CSS contract", () => {
  it("native-screens alinha tipografia da caixa visual ao editor", () => {
    const cssPath = join(dirname(fileURLToPath(import.meta.url)), "native-screens.css");
    const css = readFileSync(cssPath, "utf8");
    const baseBlock = css.match(/\.tdp-comunicado__block\s*\{([\s\S]*?)\}/);
    expect(baseBlock?.[1] ?? "").toMatch(/padding:\s*0\s*;/);
    expect(baseBlock?.[1] ?? "").not.toMatch(/padding:\s*0\.4em/);
    const typography = css.match(
      /\.tdp-comunicado__block--heading h1[\s\S]*?\.tdp-comunicado__rich-text\s*\{([\s\S]*?)\}/,
    );
    expect(typography?.[1] ?? "").toMatch(/flex:\s*0\s+0\s+auto/);
    expect(typography?.[1] ?? "").not.toMatch(/flex:\s*1\s*;/);
    expect(typography?.[1] ?? "").toMatch(/overflow:\s*visible/);
    expect(css).toMatch(/\.tdp-comunicado__shape-text\s*\{[^}]*pointer-events:\s*none/s);
    expect(css).not.toMatch(
      /\.tdp-comunicado__shape-text\s*\{[^}]*justify-content:\s*center/s,
    );
  });
});
