import { describe, expect, it } from "vitest";

import {
  PURCHASE_ORDERS_COLUMN_STORAGE_KEY,
  PURCHASE_ORDERS_TABLE_FONT_SIZE_STORAGE_KEY,
  PURCHASE_ORDERS_VIEW_LAYOUT_STORAGE_KEY,
} from "./purchaseOrdersTableConfig";
import { buildUrlSearch, createDefaultQuery, parseQueryFromSearch } from "./query";

describe("purchase orders persistence isolation", () => {
  it("keeps page storage keys isolated from purchase requests", () => {
    expect(PURCHASE_ORDERS_COLUMN_STORAGE_KEY).toBe(
      "supplies:purchase-orders:column-prefs:v1",
    );
    expect(PURCHASE_ORDERS_TABLE_FONT_SIZE_STORAGE_KEY).toBe(
      "supplies:purchase-orders:table-font-size:v1",
    );
    expect(PURCHASE_ORDERS_VIEW_LAYOUT_STORAGE_KEY).toBe(
      "supplies:purchase-orders:view-layout:v1",
    );
    expect(PURCHASE_ORDERS_COLUMN_STORAGE_KEY).not.toContain("purchase-requests");
    expect(PURCHASE_ORDERS_VIEW_LAYOUT_STORAGE_KEY).not.toContain("purchase-requests");
  });

  it("restores Todas and subset unit filters from URL after F5", () => {
    const allScope = {
      ...createDefaultQuery(),
      sort_by: "expected_delivery_date",
      sort_dir: "desc" as const,
      page: 2,
    };
    const restoredAll = parseQueryFromSearch(buildUrlSearch(allScope), ["01", "02"]);
    expect(restoredAll.branches).toEqual([]);
    expect(restoredAll.sort_by).toBe("expected_delivery_date");
    expect(restoredAll.sort_dir).toBe("desc");
    expect(restoredAll.page).toBe(2);
    expect(buildUrlSearch(allScope)).not.toContain("branch=");

    const subset = {
      ...createDefaultQuery(),
      branches: ["02"],
      page: 2,
    };
    const restoredSubset = parseQueryFromSearch(buildUrlSearch(subset), ["01", "02"]);
    expect(restoredSubset.branches).toEqual(["02"]);

    const bothInUrl = parseQueryFromSearch("?branch=01&branch=02&page=3", ["01", "02"]);
    expect(bothInUrl.branches).toEqual([]);
  });
});
