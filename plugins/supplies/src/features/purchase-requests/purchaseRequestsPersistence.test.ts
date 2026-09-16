import { describe, expect, it } from "vitest";

import {
  PURCHASE_REQUESTS_COLUMN_STORAGE_KEY,
  PURCHASE_REQUESTS_TABLE_FONT_SIZE_STORAGE_KEY,
  PURCHASE_REQUESTS_VIEW_LAYOUT_STORAGE_KEY,
} from "./purchaseRequestsTableConfig";
import { buildUrlSearch, createDefaultQuery, parseQueryFromSearch } from "./query";

describe("purchase requests persistence isolation", () => {
  it("keeps page storage keys isolated from purchase orders", () => {
    expect(PURCHASE_REQUESTS_COLUMN_STORAGE_KEY).toBe(
      "supplies:purchase-requests:column-prefs:v1",
    );
    expect(PURCHASE_REQUESTS_TABLE_FONT_SIZE_STORAGE_KEY).toBe(
      "supplies:purchase-requests:table-font-size:v1",
    );
    expect(PURCHASE_REQUESTS_VIEW_LAYOUT_STORAGE_KEY).toBe(
      "supplies:purchase-requests:view-layout:v1",
    );
    expect(PURCHASE_REQUESTS_COLUMN_STORAGE_KEY).not.toContain("purchase-orders");
    expect(PURCHASE_REQUESTS_VIEW_LAYOUT_STORAGE_KEY).not.toContain("purchase-orders");
  });

  it("restores Todas and subset unit filters from URL after F5", () => {
    const allScope = {
      ...createDefaultQuery(),
      sort_by: "issue_date",
      sort_dir: "asc" as const,
      page: 2,
    };
    const restoredAll = parseQueryFromSearch(buildUrlSearch(allScope), ["01", "02"]);
    expect(restoredAll.branches).toEqual([]);
    expect(restoredAll.sort_by).toBe("issue_date");
    expect(restoredAll.sort_dir).toBe("asc");
    expect(restoredAll.page).toBe(2);
    expect(buildUrlSearch(allScope)).not.toContain("branch=");

    const stageScope = {
      ...createDefaultQuery(),
      sort_by: "overall_stage",
      sort_dir: "desc" as const,
      product_code: "MP01",
    };
    const restoredStage = parseQueryFromSearch(buildUrlSearch(stageScope), ["01", "02"]);
    expect(restoredStage.sort_by).toBe("overall_stage");
    expect(restoredStage.sort_dir).toBe("desc");
    expect(restoredStage.product_code).toBe("MP01");
    expect(buildUrlSearch(stageScope)).not.toContain("period=");

    const subset = {
      ...createDefaultQuery(),
      branches: ["01"],
      page: 2,
    };
    const restoredSubset = parseQueryFromSearch(buildUrlSearch(subset), ["01", "02"]);
    expect(restoredSubset.branches).toEqual(["01"]);
    expect(restoredSubset.page).toBe(2);

    const bothInUrl = parseQueryFromSearch("?branch=01&branch=02&page=3", ["01", "02"]);
    expect(bothInUrl.branches).toEqual([]);
    expect(bothInUrl.page).toBe(3);
  });
});
