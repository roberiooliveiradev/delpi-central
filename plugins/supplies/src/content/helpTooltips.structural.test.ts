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
    expect(SP_HELP.overviewChartSeriesPicker.length).toBeGreaterThan(20);
    expect(SP_HELP.overviewChartSeriesAppearance.length).toBeGreaterThan(20);
    expect(SP_HELP.overviewChartSeriesColor.length).toBeGreaterThan(20);
    expect(SP_HELP.overviewFiltersBranch.length).toBeGreaterThan(20);
    expect(SP_HELP.otdAnalyticsPage.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseRequests.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseRequestsBranch.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseRequestsView.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseRequestsSort.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrders.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersBranch.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersDelivery.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersFilters.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersView.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersSort.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersExcel.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersTableFontSize.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersTableColumns.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersTableMeta.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersCardsMeta.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseRequestsTableFontSize.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseRequestsTableColumns.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseRequestsTableMeta.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseRequestsCardsMeta.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseRequestsFilters.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseRequestsRefresh.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrdersColOpenQty.length).toBeGreaterThan(10);
    expect(SP_HELP.purchaseRequestsColStage.length).toBeGreaterThan(10);
    expect(SP_HELP.purchaseRequestDetail.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrderDetail.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrderDetailItems.length).toBeGreaterThan(20);
    expect(SP_HELP.purchaseOrderDetailReceipts.length).toBeGreaterThan(20);
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
