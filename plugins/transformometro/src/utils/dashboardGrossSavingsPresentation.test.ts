import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const source = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "dashboardGrossSavingsPresentation.ts"),
  "utf8",
);

describe("buildGrossSavingsKpiPresentation", () => {
  it("compõe o kit SI e não recalcula IDD no Transformômetro", () => {
    expect(source).toMatch(/buildKpiGoalPresentation/);
    expect(source).toMatch(/pickSiIddScoreLabel/);
    expect(source).toMatch(/buildSiIndicatorScoreMap/);
    expect(source).toMatch(/STRATEGIC_INDICATORS_GROSS_SAVINGS_INDICATOR_ID/);
    expect(source).toMatch(/iddScoreLabel/);
    expect(source).not.toMatch(/calculateIndicatorIddScore/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
  });
});
