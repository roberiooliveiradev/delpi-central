import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const cssPath = resolve(dirname(fileURLToPath(import.meta.url)), "./select-control.css");

describe("select-control scroll contract", () => {
  it("painel portaled não compete com a lista em overflow:auto", () => {
    const css = readFileSync(cssPath, "utf8");
    const portalBlockMatch = css.match(
      /\.delpi-ui-select__panel--portal[\s\S]*?\{([\s\S]*?)\}/,
    );
    const portalBody = (portalBlockMatch?.[1] ?? "").replace(/\/\*[\s\S]*?\*\//g, "");

    expect(portalBody).toMatch(/overflow:\s*hidden\s*;/);
    expect(portalBody).not.toMatch(/overflow:\s*auto\s*;/);

    const nestedListBlockMatch = css.match(
      /\.delpi-ui-select__panel--portal\s+\.delpi-ui-select__list[\s\S]*?\{([\s\S]*?)\}/,
    );
    const nestedListBody = (nestedListBlockMatch?.[1] ?? "").replace(/\/\*[\s\S]*?\*\//g, "");

    expect(nestedListBody).toMatch(/overflow:\s*auto\s*;/);
    expect(nestedListBody).toMatch(/max-height:\s*none\s*;/);
  });
});
