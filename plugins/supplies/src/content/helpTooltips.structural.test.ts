import { describe, expect, it } from "vitest";

import { SP_HELP } from "./helpTooltips";

function collectStrings(value: unknown, acc: string[] = []): string[] {
  if (typeof value === "string") {
    acc.push(value);
    return acc;
  }
  if (value && typeof value === "object") {
    for (const nested of Object.values(value as Record<string, unknown>)) {
      collectStrings(nested, acc);
    }
  }
  return acc;
}

describe("helpTooltips", () => {
  it("keeps required shell help keys", () => {
    expect(SP_HELP.coexistence.length).toBeGreaterThan(20);
    expect(SP_HELP.homeVsOverview.length).toBeGreaterThan(20);
    expect(SP_HELP.homeAttention.length).toBeGreaterThan(20);
    expect(SP_HELP.home.attention).toBe(SP_HELP.homeAttention);
    expect(SP_HELP.home.paths.length).toBeGreaterThan(20);
    expect(SP_HELP.home.search.length).toBeGreaterThan(20);
    expect(SP_HELP.home.favorites.length).toBeGreaterThan(20);
    expect(SP_HELP.home.recents.length).toBeGreaterThan(20);
    expect(SP_HELP.home.sections.operations.length).toBeGreaterThan(20);
    expect(SP_HELP.overviewTemporal.length).toBeGreaterThan(20);
    expect(SP_HELP.overviewFiltersPeriod.length).toBeGreaterThan(20);
    expect(SP_HELP.overviewGoalTriad.length).toBeGreaterThan(20);
    expect(SP_HELP.overviewOtdChart.length).toBeGreaterThan(20);
    expect(SP_HELP.overviewCompareChart.length).toBeGreaterThan(20);
    expect(SP_HELP.overviewFiltersBranch.length).toBeGreaterThan(20);
    expect(SP_HELP.otdAnalyticsPage.length).toBeGreaterThan(20);
    expect(SP_HELP.forbiddenUnit.length).toBeGreaterThan(20);
    expect(SP_HELP.userProfile.length).toBeGreaterThan(20);
    expect(SP_HELP.userProfilePrefs.length).toBeGreaterThan(20);
    expect(SP_HELP.shell.navHome).toBeTruthy();
    expect(SP_HELP.shell.navOverview).toBeTruthy();
  });

  it("does not leak technical identifiers in help copy", () => {
    const texts = collectStrings(SP_HELP);
    for (const text of texts) {
      expect(text).not.toMatch(/operationId|\/apps\/supplies-api|GET \//);
    }
  });
});
