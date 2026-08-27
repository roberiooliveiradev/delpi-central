import { describe, expect, it } from "vitest";

import { buildUrlSearch, parseRequestKey, parseUrlState, searchHasExplicitFilters } from "./urlState";

describe("urlState", () => {
  it("parses and serializes filters in query string", () => {
    const state = parseUrlState(
      "?branch=02&date_from=2026-08-01&date_to=2026-08-31&page=2&overall_stage=awaiting_order&request=02:164708",
      "01",
    );
    expect(state.branch).toBe("02");
    expect(state.page).toBe(2);
    expect(state.overall_stages).toEqual(["awaiting_order"]);
    expect(state.request).toBe("02:164708");
    expect(buildUrlSearch(state)).toContain("branch=02");
    expect(buildUrlSearch(state)).toContain("page=2");
    expect(buildUrlSearch(state)).toContain("overall_stage=awaiting_order");
  });

  it("parses and serializes requester, stage and cost-center lists", () => {
    const state = parseUrlState(
      "?branch=01&requester=USR01,USR02&cost_center=0413,0520&overall_stage=awaiting_order,awaiting_receipt",
      "01",
    );
    expect(state.requester_user_ids).toEqual(["USR01", "USR02"]);
    expect(state.cost_center_codes).toEqual(["0413", "0520"]);
    expect(state.overall_stages).toEqual(["awaiting_order", "awaiting_receipt"]);
    expect(buildUrlSearch(state)).toContain("requester=USR01%2CUSR02");
    expect(buildUrlSearch(state)).toContain("cost_center=0413%2C0520");
    expect(buildUrlSearch(state)).toContain("overall_stage=awaiting_order%2Cawaiting_receipt");
  });

  it("prefers repeated requester_user_id over comma list", () => {
    const state = parseUrlState(
      "?branch=01&requester=USR01,USR02&requester_user_id=USR03",
      "01",
    );
    expect(state.requester_user_ids).toEqual(["USR03"]);
  });

  it("parses request key for detail drawer", () => {
    expect(parseRequestKey("02:164708")).toEqual({
      branch: "02",
      requestNumber: "164708",
    });
  });

  it("detects empty vs explicit URL filters", () => {
    expect(searchHasExplicitFilters("")).toBe(false);
    expect(searchHasExplicitFilters("?")).toBe(false);
    expect(searchHasExplicitFilters("?request=02:164708")).toBe(true);
  });
});
