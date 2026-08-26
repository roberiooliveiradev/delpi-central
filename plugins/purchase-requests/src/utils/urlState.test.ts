import { describe, expect, it } from "vitest";

import { buildUrlSearch, parseRequestKey, parseUrlState } from "./urlState";

describe("urlState", () => {
  it("parses and serializes filters in query string", () => {
    const state = parseUrlState(
      "?branch=02&date_from=2026-08-01&date_to=2026-08-31&page=2&overall_stage=awaiting_order&request=02:164708",
      "01",
    );
    expect(state.branch).toBe("02");
    expect(state.page).toBe(2);
    expect(state.overall_stage).toBe("awaiting_order");
    expect(state.request).toBe("02:164708");
    expect(buildUrlSearch(state)).toContain("branch=02");
    expect(buildUrlSearch(state)).toContain("page=2");
  });

  it("parses and serializes requester multiselect in query string", () => {
    const state = parseUrlState(
      "?branch=01&requester=USR01,USR02&requester_user_id=USR03",
      "01",
    );
    expect(state.requester_user_ids).toEqual(["USR03"]);
    const fromComma = parseUrlState("?branch=01&requester=USR01,USR02", "01");
    expect(fromComma.requester_user_ids).toEqual(["USR01", "USR02"]);
    expect(buildUrlSearch({ ...fromComma, requester_user_ids: ["A", "B"] })).toContain(
      "requester=A%2CB",
    );
  });

  it("parses request key for detail drawer", () => {
    expect(parseRequestKey("02:164708")).toEqual({
      branch: "02",
      requestNumber: "164708",
    });
  });
});
