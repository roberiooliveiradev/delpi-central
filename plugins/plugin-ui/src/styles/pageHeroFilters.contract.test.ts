import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const css = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "page-hero.css"),
  "utf8",
);

describe("page-hero.css — filtros flush no hero", () => {
  it("mantém PageHero como card (fundo/borda)", () => {
    expect(css).toMatch(/\.delpi-ui-page-hero\s*\{[^}]*box-shadow:/s);
    expect(css).toMatch(/\.delpi-ui-page-hero\s*\{[^}]*border:\s*1px solid/s);
  });

  it("FilterBar e FiltersRow dentro do hero ficam sem chrome próprio", () => {
    expect(css).toMatch(
      /\.delpi-ui-page-hero \.delpi-ui-filter-bar(?::not\(\.delpi-ui-card\))?[^,{]*[,{][^}]*border:\s*none/s,
    );
    expect(css).toMatch(
      /\.delpi-ui-page-hero \.delpi-ui-filters-row\s*\{[^}]*border:\s*none/s,
    );
    expect(css).toMatch(
      /\.delpi-ui-page-hero \.delpi-ui-filters-row\s*\{[^}]*background:\s*transparent/s,
    );
  });
});
