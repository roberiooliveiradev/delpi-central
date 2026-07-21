import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Contrato: tipografia em caixa visual alinhada ao editor.
 * CSS canônico: plugin-ui/styles/comunicado-stage.css (`.delpi-ui-comunicado*`).
 */
describe("visual box typography CSS contract", () => {
  it("comunicado-stage (plugin-ui) alinha tipografia da caixa visual ao editor", () => {
    const cssPath = join(
      dirname(fileURLToPath(import.meta.url)),
      "../../plugin-ui/src/styles/comunicado-stage.css",
    );
    const css = readFileSync(cssPath, "utf8");
    const baseBlock = css.match(/\.delpi-ui-comunicado__block\s*\{([\s\S]*?)\}/);
    expect(baseBlock?.[1] ?? "").toMatch(/padding:\s*0\s*;/);
    expect(baseBlock?.[1] ?? "").not.toMatch(/padding:\s*0\.4em/);
    const typography = css.match(
      /\.delpi-ui-comunicado__block--heading h1[\s\S]*?\.delpi-ui-comunicado__rich-text\s*\{([\s\S]*?)\}/,
    );
    expect(typography?.[1] ?? "").toMatch(/flex:\s*0\s+0\s+auto/);
    expect(typography?.[1] ?? "").not.toMatch(/flex:\s*1\s*;/);
    expect(typography?.[1] ?? "").toMatch(/overflow:\s*visible/);
    expect(css).toMatch(/\.delpi-ui-comunicado__shape-text\s*\{[^}]*pointer-events:\s*none/s);
    expect(css).not.toMatch(
      /\.delpi-ui-comunicado__shape-text\s*\{[^}]*justify-content:\s*center/s,
    );
  });

  it("native-screens não espelha paint do comunicado", () => {
    const nativePath = join(dirname(fileURLToPath(import.meta.url)), "native-screens.css");
    const native = readFileSync(nativePath, "utf8");
    expect(native).not.toMatch(/\.tdp-comunicado\s*\{/);
    expect(native).not.toMatch(/\.tdp-comunicado__/);
    expect(native).not.toMatch(/\.delpi-ui-comunicado/);
  });
});
