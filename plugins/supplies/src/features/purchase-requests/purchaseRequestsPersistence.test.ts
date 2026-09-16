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

  it("restores multi-unit and sort from URL after F5", () => {
    const query = {
      ...createDefaultQuery(["01", "02"]),
      sort_by: "issue_date",
      sort_dir: "asc" as const,
      page: 2,
    };
    const restored = parseQueryFromSearch(buildUrlSearch(query), ["01"]);
    expect(restored.branches).toEqual(["01", "02"]);
    expect(restored.sort_by).toBe("issue_date");
    expect(restored.sort_dir).toBe("asc");
    expect(restored.page).toBe(2);
  });
});
