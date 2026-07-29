import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Editor selecionado ≠ TV ociosa: overflow:hidden só sem seleção clipava a
 * legenda («FM» vs «FM - FALHA…»). Shell/chart devem ser visible sempre.
 */
describe("series chart legend overflow parity (editor ≡ present)", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const css = readFileSync(join(base, "../../styles/series-chart.css"), "utf8");
  const primitive = readFileSync(join(base, "SeriesChartPrimitive.tsx"), "utf8");

  it("shell e chart não gateiam overflow na seleção", () => {
    expect(css).toMatch(
      /\.delpi-ui-series-chart-shell\s*\{[^}]*overflow:\s*visible/s,
    );
    expect(css).toMatch(/\.delpi-ui-series-chart\s*\{[^}]*overflow:\s*visible/s);
    expect(css).not.toMatch(
      /\.delpi-ui-series-chart-shell:has\([^)]*part--selected[^)]*\)\s*\{[^}]*overflow:\s*visible/s,
    );
    expect(primitive).toMatch(/overflow:\s*[\"']visible[\"']/);
    expect(primitive).not.toMatch(/chartAreaSelected\s*\?\s*[\"']visible[\"']/);
  });
});
