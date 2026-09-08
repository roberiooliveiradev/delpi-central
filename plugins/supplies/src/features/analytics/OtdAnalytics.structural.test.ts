import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { buildOtdAggregateQuery } from "../../api/otd";
import { canAccessView } from "../../app/routeAccess";
import { buildPluginPath, resolvePluginRoute } from "../../app/pluginRoutes";

const here = dirname(fileURLToPath(import.meta.url));

describe("OTD analytics page", () => {
  it("resolves analytics/otd route and requires analytics capability", () => {
    expect(resolvePluginRoute("/apps/supplies/analytics/otd").view).toBe("analytics_otd");
    expect(buildPluginPath("analytics_otd")).toBe("/apps/supplies/analytics/otd");
    expect(
      canAccessView("analytics_otd", {
        portal: true,
        purchaseRequests: false,
        operations: false,
        analytics: false,
        administration: false,
        viewAll: false,
        export: false,
      }),
    ).toBe(false);
    expect(
      canAccessView("analytics_otd", {
        portal: true,
        purchaseRequests: false,
        operations: false,
        analytics: true,
        administration: false,
        viewAll: false,
        export: false,
      }),
    ).toBe(true);
  });

  it("uses SpeedometerGauge, MultiSelect filters and series chart", () => {
    const page = readFileSync(join(here, "OtdAnalyticsPage.tsx"), "utf8");
    expect(page).toContain("SuppliesSpeedometerGauge");
    expect(page).toContain("OverviewFilters");
    expect(page).toContain("OverviewOtdSeriesChart");
    expect(page).toContain("getOtdAggregate");
    expect(page).toContain("formatOperationalUnitCode");
    expect(page).not.toMatch(/from ["']@delpi\/plugin-ui/);
  });

  it("builds aggregate query", () => {
    expect(buildOtdAggregateQuery({ branch: "01", from: "2026-09-01", to: "2026-09-30" })).toBe(
      "?branch=01&from=2026-09-01&to=2026-09-30",
    );
    expect(buildOtdAggregateQuery({})).toBe("");
  });
});
