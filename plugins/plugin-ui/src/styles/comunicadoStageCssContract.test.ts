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

  it("clipa o retângulo de design e não herda grid KPI", () => {
    expect(css).toMatch(/\.tdp-native-screen\.delpi-ui-comunicado\s*\{[^}]*display:\s*block/s);
    const root = css.match(/(?:^|[\s,}])\.delpi-ui-comunicado\s*\{([\s\S]*?)\}/m);
    expect(root?.[1] ?? "").toMatch(/overflow:\s*hidden/);
    expect(css).toMatch(/\.delpi-ui-comunicado__stage\s*\{[^}]*position:\s*absolute[^}]*inset:\s*0/s);
  });

  it("tipografia da caixa visual sem padding no wrapper nem flex:1", () => {
    const baseBlock = css.match(/\.delpi-ui-comunicado__block\s*\{([\s\S]*?)\}/);
    expect(baseBlock?.[1] ?? "").toMatch(/padding:\s*0\s*;/);
    expect(baseBlock?.[1] ?? "").not.toMatch(/padding:\s*0\.4em/);
    expect(css).toMatch(/flex:\s*0\s+0\s+auto/);
    expect(css).toMatch(/\.delpi-ui-comunicado__shape-text\s*\{[^}]*pointer-events:\s*none/s);
  });
});
