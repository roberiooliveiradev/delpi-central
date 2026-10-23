import { describe, expect, it } from "vitest";

import {
  PURCHASE_REQUESTS_COLUMN_STORAGE_KEY,
  PURCHASE_REQUESTS_TABLE_FONT_SIZE_STORAGE_KEY,
  PURCHASE_REQUESTS_VIEW_LAYOUT_STORAGE_KEY,
} from "./purchaseRequestsTableConfig";
import { buildUrlSearch, createDefaultQuery, parseQueryFromSearch } from "./query";

describe("purchase requests persistence isolation", () => {
  it("round-trips requester and cost-center filters through the URL", () => {
    const scope = {
      ...createDefaultQuery(),
      requester_ids: ["000304", "000313"],
      cost_centers: ["0413", "0520"],
    };
    const qs = buildUrlSearch(scope);
    expect(qs).toContain("requester_user_id=000304");
    expect(qs).toContain("requester_user_id=000313");
    expect(qs).toContain("cost_center=0413");
    expect(qs).toContain("cost_center=0520");
    const restored = parseQueryFromSearch(qs, ["01", "02"]);
    expect(restored.requester_ids).toEqual(["000304", "000313"]);
    expect(restored.cost_centers).toEqual(["0413", "0520"]);
    // Leading zeros survive the round-trip.
    expect(restored.requester_ids[0]).toBe("000304");
    const cleared = parseQueryFromSearch("", ["01", "02"]);
    expect(cleared.requester_ids).toEqual([]);
    expect(cleared.cost_centers).toEqual([]);
  });

  it("repeats requester_user_id and cost_center for the API contract", () => {
    const scope = {
      ...createDefaultQuery(),
      requester_ids: ["000304"],
      cost_centers: ["0413"],
    };
    const qs = buildUrlSearch(scope);
    expect(qs.match(/requester_user_id=/g)).toHaveLength(1);
    expect(qs.match(/cost_center=/g)).toHaveLength(1);
  });

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
