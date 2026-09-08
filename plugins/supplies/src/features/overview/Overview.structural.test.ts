import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { buildOtdSeriesQuery } from "../../api/otdSeries";

const here = dirname(fileURLToPath(import.meta.url));

describe("Overview structural", () => {
  it("uses PageHero, FilterBar kit, SectionCard and ChartViewShell", () => {
    const page = readFileSync(join(here, "../../pages/OverviewPage.tsx"), "utf8");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("OverviewFilters");
    expect(page).toContain("SuppliesSectionCard");
    expect(page).toContain("OverviewOtdSeriesChart");
    expect(page).toContain("OverviewCompareChart");
    expect(page).not.toContain("<select");
    expect(page).not.toContain('type="date"');

    const filters = readFileSync(join(here, "OverviewFilters.tsx"), "utf8");
    expect(filters).toContain("SuppliesFilterBarShell");
    expect(filters).toContain("SuppliesDateField");
    expect(filters).toContain("SuppliesSelectField");
    expect(filters).toContain("SuppliesSegmentToggle");

    const otd = readFileSync(join(here, "OverviewOtdSeriesChart.tsx"), "utf8");
    expect(otd).toContain("ChartViewShell");
    expect(otd).toContain("getOtdSeries");
    expect(otd).toContain("MultiTypeSeriesChart");

    const compare = readFileSync(join(here, "OverviewCompareChart.tsx"), "utf8");
    expect(compare).toContain("ChartViewShell");
    expect(compare).toContain("temporalNature === \"interval\"");
  });

  it("builds otd series query for positive and sibling cases", () => {
    expect(
      buildOtdSeriesQuery({
        branch: "01",
        from: "2026-09-01",
        to: "2026-09-30",
        granularity: "month",
      }),
    ).toBe("?branch=01&from=2026-09-01&to=2026-09-30&granularity=month");
    expect(buildOtdSeriesQuery({ from: "2026-01-01", to: "2026-12-31" })).toBe(
      "?from=2026-01-01&to=2026-12-31",
    );
    expect(buildOtdSeriesQuery({})).toBe("");
  });
});
