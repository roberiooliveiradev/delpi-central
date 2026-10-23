import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const multiSelectCssPath = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "./multi-select.css",
);
const selectControlCssPath = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "./select-control.css",
);

describe("multi-select portal scroll contract", () => {
  it("painel portaled limita altura com overflow:hidden e a lista é a única superfície rolável", () => {
    const css = readFileSync(multiSelectCssPath, "utf8");

    const portalBlockMatch = css.match(
      /\.delpi-ui-multi-select__panel--portal[\s\S]*?\{([\s\S]*?)\}/,
    );
    const portalBody = (portalBlockMatch?.[1] ?? "").replace(/\/\*[\s\S]*?\*\//g, "");

    expect(portalBody).toMatch(/overflow:\s*hidden\s*;/);
    expect(portalBody).toMatch(/max-height:\s*min\(70vh,\s*480px\)\s*;/);
    expect(portalBody).toMatch(/display:\s*flex\s*;/);
    expect(portalBody).toMatch(/flex-direction:\s*column\s*;/);

    const nestedListBlockMatch = css.match(
      /\.delpi-ui-multi-select__panel--portal\s+\.delpi-ui-multi-select__list[\s\S]*?\{([\s\S]*?)\}/,
    );
    const nestedListBody = (nestedListBlockMatch?.[1] ?? "").replace(/\/\*[\s\S]*?\*\//g, "");

    expect(nestedListBody).toMatch(/overflow:\s*auto\s*;/);
    expect(nestedListBody).toMatch(/max-height:\s*none\s*;/);
    expect(nestedListBody).toMatch(/flex:\s*1\s+1\s+auto\s*;/);
  });

  it("wildcards do select-control não vazam para classes -multi-select__*", () => {
    const css = readFileSync(selectControlCssPath, "utf8");
    // "-select__*" é substring de "-multi-select__*": todo wildcard do select
    // precisa estar negado com :not([class*="-multi-select__..."]) para não
    // capturar o painel/lista do multi-select portaled.
    const wildcardSelectors = css.match(/\[class\*="-select__[^\]]*"\][^{,]*/g) ?? [];

    expect(wildcardSelectors.length).toBeGreaterThan(0);
    for (const selector of wildcardSelectors) {
      expect(selector).toContain('not([class*="-multi-select__');
    }
  });
});
