import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const css = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "page-hero.css"),
  "utf8",
);

describe("page-hero.css — uma moldura de filtros no hero", () => {
  it("mantém PageHero como card (fundo/borda)", () => {
    expect(css).toMatch(/\.delpi-ui-page-hero\s*\{[^}]*box-shadow:/s);
    expect(css).toMatch(/\.delpi-ui-page-hero\s*\{[^}]*border:\s*1px solid/s);
  });

  it("não zera a moldura do FilterBar dentro do hero", () => {
    expect(css).not.toMatch(
      /\.delpi-ui-page-hero \.delpi-ui-filter-bar(?::not\(\.delpi-ui-card\))?[^,{]*[,{][^}]*border:\s*none/s,
    );
  });

  it("FiltersRow no hero fica sem moldura própria (evita borda dupla)", () => {
    expect(css).toMatch(
      /\.delpi-ui-page-hero \.delpi-ui-filters-row\s*\{[^}]*border:\s*none/s,
    );
    expect(css).toMatch(
      /\.delpi-ui-page-hero \.delpi-ui-filters-row\s*\{[^}]*background:\s*transparent/s,
    );
  });
});
