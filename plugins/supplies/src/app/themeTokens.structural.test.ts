import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const css = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "../index.css"),
  "utf8",
);

describe("Supplies theme tokens (Commercial parity)", () => {
  it("maps light/dark surfaces into delpi-ui card tokens", () => {
    expect(css).toContain("--delpi-ui-surface: var(--sp-surface)");
    expect(css).toContain("--sp-surface: var(--surface, #ffffff)");
    expect(css).toContain(
      "--sp-surface: color-mix(in srgb, var(--surface-2, #1b2030) 82%, black)",
    );
    expect(css).toContain("--sp-border: rgba(255, 255, 255, 0.14)");
  });

  it("uses primary as dark brand/title without pastel white mix", () => {
    expect(css).toContain(".theme-dark .dashboard-supplies-portal");
    expect(css).toContain("--sp-brand: var(--primary, #089bdb)");
    expect(css).not.toContain("72%, white");
  });

  it("keeps KPI value title token white in dark and brand in light", () => {
    expect(css).toMatch(
      /\.dashboard-supplies-portal \{[\s\S]*?--delpi-ui-title: var\(--sp-brand\)/,
    );
    expect(css).toContain("/* Valor do KPI: texto branco (paridade Comercial)");
    expect(css).toContain("--delpi-ui-title: var(--sp-text)");
  });
});
