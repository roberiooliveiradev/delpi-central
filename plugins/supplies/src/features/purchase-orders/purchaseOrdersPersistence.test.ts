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

  it("restores multi-unit and sort from URL after F5", () => {
    const query = {
      ...createDefaultQuery(["01", "02"]),
      sort_by: "expected_delivery_date",
      sort_dir: "desc" as const,
      page: 2,
    };
    const restored = parseQueryFromSearch(buildUrlSearch(query), ["01"]);
    expect(restored.branches).toEqual(["01", "02"]);
    expect(restored.sort_by).toBe("expected_delivery_date");
    expect(restored.sort_dir).toBe("desc");
    expect(restored.page).toBe(2);
  });
});
