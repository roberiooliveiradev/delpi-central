import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Regressão: handles de resize do gráfico vivem em plugin-ui/series-chart.css
 * (prefixo `delpi-ui-series-chart`). Sem position:absolute, os botões ficam em linha no título.
 */
describe("series chart part resize CSS (plugin-ui)", () => {
  const css = readFileSync(
    join(
      dirname(fileURLToPath(import.meta.url)),
      "../../plugin-ui/src/styles/series-chart.css",
    ),
    "utf8",
  );

  const nativeCss = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "native-screens.css"),
    "utf8",
  );

  it("define position absolute nos handles delpi-ui", () => {
    expect(css).toMatch(/\.delpi-ui-series-chart__part--resizable\s*\{[^}]*position:\s*relative/);
    expect(css).toMatch(/\.delpi-ui-series-chart__part-resize\s*\{[^}]*position:\s*absolute/);
    for (const handle of ["nw", "n", "ne", "e", "se", "s", "sw", "w"] as const) {
      expect(css).toContain(`.delpi-ui-series-chart__part-resize--${handle}`);
    }
  });

  it("native-screens não duplica paint tdp-series-chart nem chrome do kit", () => {
    expect(nativeCss).not.toMatch(/\.tdp-series-chart\s*\{/);
    expect(nativeCss).not.toMatch(/\.delpi-ui-/);
    expect(nativeCss).not.toMatch(/\.delpi-kpi-/);
    expect(css).toMatch(/\.delpi-ui-series-chart-shell\s*\{[^}]*box-shadow:\s*var\(\s*--tdp-block-box-shadow/s);
  });

  it("comunicado não herda grid KPI (prévia/filmstrip em branco)", () => {
    expect(nativeCss).toMatch(/\.tdp-native-screen\.tdp-comunicado\s*\{[^}]*display:\s*block/);
    expect(nativeCss).toMatch(/\.tdp-comunicado__stage\s*\{[^}]*position:\s*absolute[^}]*inset:\s*0/s);
  });
});
