import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

function source(relativePath: string): string {
  return readFileSync(join(here, relativePath), "utf8");
}

function sliceBetween(text: string, start: string, end: string): string {
  const from = text.indexOf(start);
  const to = text.indexOf(end, from + start.length);
  return from >= 0 && to > from ? text.slice(from, to) : text;
}

describe("Line feeder product detail wiring", () => {
  it("abre o detalhe pelo clique na linha da necessidade", () => {
    const page = source("./LineFeederPage.tsx");
    expect(page).toMatch(/onRowClick=\{\(row\) => setSelectedProductCode\(row\.product_code\)\}/);
    expect(page).toMatch(/fetchLineFeederProductDetail/);
    expect(page).toMatch(/LineFeederProductDetailModal/);
    expect(page).not.toMatch(/\/apps\/api-delpi/);
  });

  it("não vaza códigos técnicos de estoque na copy nem na ajuda", () => {
    const copy = sliceBetween(source("../content/copy.ts"), "lineFeeder:", "materials:");
    const help = sliceBetween(
      source("../content/helpTooltips.ts"),
      "lineFeeder:",
      "lineFeederPickPlan:",
    );
    for (const leak of ["SD3", "D3_CF", "SB2", "DE0", "RE0", "PR0"]) {
      expect(copy).not.toContain(leak);
      expect(help).not.toContain(leak);
    }
    expect(help).toContain("Clique na linha");
  });
});
