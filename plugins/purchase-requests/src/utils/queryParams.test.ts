import { describe, expect, it } from "vitest";

import { buildListQueryParams, buildListSearchParams } from "./queryParams";

describe("buildListQueryParams", () => {
  it("includes supported filters and pagination", () => {
    const search = buildListSearchParams({
      branch: "02",
      date_from: "2026-08-01",
      date_to: "2026-08-31",
      request_number: "177030",
      requester_user_ids: [],
      cost_center_codes: ["0413"],
      product_code: "51000016",
      supplier_code: "000001",
      order_number: "041446",
      overall_stages: ["awaiting_order"],
      page: 2,
      page_size: 25,
    });
    expect(Object.fromEntries(search.entries())).toEqual({
      branch: "02",
      date_from: "2026-08-01",
      date_to: "2026-08-31",
      request_number: "177030",
      cost_center: "0413",
      product_code: "51000016",
      supplier_code: "000001",
      order_number: "041446",
      overall_stage: "awaiting_order",
      page: "2",
      page_size: "25",
    });
  });

  it("omits empty optional filters", () => {
    expect(
      buildListQueryParams({
        branch: "01",
        date_from: "",
        date_to: "",
        request_number: "",
        requester_user_ids: [],
        cost_center_codes: [],
        product_code: "",
        supplier_code: "",
        order_number: "",
        overall_stages: [],
        page: 1,
        page_size: 50,
      }),
    ).toEqual({
      branch: "01",
      page: "1",
      page_size: "50",
    });
  });

  it("appends multiple requester, cost center and stage params", () => {
    const search = buildListSearchParams({
      branch: "01",
      requester_user_ids: ["USR01", "USR02"],
      cost_center_codes: ["0413", "0520"],
      overall_stages: ["awaiting_order", "awaiting_receipt"],
      page: 1,
      page_size: 50,
    });
    expect(search.getAll("requester_user_id")).toEqual(["USR01", "USR02"]);
    expect(search.getAll("cost_center")).toEqual(["0413", "0520"]);
    expect(search.getAll("overall_stage")).toEqual(["awaiting_order", "awaiting_receipt"]);
  });
});
