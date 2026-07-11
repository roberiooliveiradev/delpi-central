import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Regressão: prefixo `tdp-series-chart` no TV precisa espelhar os handles
 * de resize do plugin-ui — sem CSS absoluto, os botões ficam em linha no título.
 */
describe("native-screens chart part resize CSS", () => {
  const css = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "native-screens.css"),
    "utf8",
  );

  it("define position absolute nos handles tdp (não só delpi-ui)", () => {
    expect(css).toMatch(/\.tdp-series-chart__part--resizable\s*\{[^}]*position:\s*relative/);
    expect(css).toMatch(/\.tdp-series-chart__part-resize\s*\{[^}]*position:\s*absolute/);
    for (const handle of ["nw", "n", "ne", "e", "se", "s", "sw", "w"] as const) {
      expect(css).toContain(`.tdp-series-chart__part-resize--${handle}`);
    }
  });
});
