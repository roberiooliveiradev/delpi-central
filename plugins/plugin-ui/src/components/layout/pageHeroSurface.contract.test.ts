import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const css = readFileSync(join(here, "../../styles/page-hero.css"), "utf8");

describe("PageHero surface contract (CSS)", () => {
  it("default root não usa chrome de card (borda/sombra/fundo opaco)", () => {
    expect(css).toMatch(
      /\.delpi-ui-page-hero\s*\{[^}]*background:\s*transparent/s,
    );
    expect(css).toMatch(/\.delpi-ui-page-hero\s*\{[^}]*border:\s*none/s);
    expect(css).toMatch(/\.delpi-ui-page-hero\s*\{[^}]*box-shadow:\s*none/s);
  });

  it("featured restaura card legado", () => {
    expect(css).toMatch(/\.delpi-ui-page-hero--featured\s*\{[^}]*box-shadow:/s);
    expect(css).toMatch(/\.delpi-ui-page-hero--featured\s*\{[^}]*border-radius:\s*28px/s);
  });

  it("aninha .delpi-ui-card sem chrome dentro do hero", () => {
    expect(css).toMatch(
      /\.delpi-ui-page-hero \.delpi-ui-card\s*\{[^}]*box-shadow:\s*none/s,
    );
    expect(css).toMatch(
      /\.delpi-ui-page-hero \.delpi-ui-card\s*\{[^}]*border:\s*none/s,
    );
  });
});
