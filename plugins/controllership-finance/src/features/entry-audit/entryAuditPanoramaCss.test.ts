/**
 * U14R H1 — não voltar a estilizar internos do kit via [class*=…].
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const CSS = readFileSync(join(__dirname, "../../index.css"), "utf8");

describe("U14R H1 — CSS do Panorama sem attribute selectors no kit", () => {
  it("não usa [class*=…] sob panorama/conformity/severity", () => {
    const panoramaBlocks = CSS.match(
      /\.cf-analysis-panorama[\s\S]*?(?=@media|\.dashboard-controllership-finance \.cf-analysis-(?!panorama)|$)/g,
    );
    const haystack = panoramaBlocks?.join("\n") ?? CSS;
    expect(haystack).not.toMatch(/\[class\*=/);
  });

  it("não aplica min-height genérico a semicircle/distribution-donut via substring", () => {
    expect(CSS).not.toMatch(
      /\[class\*="semicircle"\][\s\S]{0,80}min-height/,
    );
    expect(CSS).not.toMatch(
      /\[class\*="distribution-donut"\][\s\S]{0,80}min-height/,
    );
  });

  it("panorama-row alinha ao topo (não stretch)", () => {
    expect(CSS).toMatch(
      /\.cf-analysis-panorama-row\s*\{[^}]*align-items:\s*start/s,
    );
  });
});
