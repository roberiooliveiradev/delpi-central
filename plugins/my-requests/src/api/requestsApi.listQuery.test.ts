import { describe, expect, it } from "vitest";

import { buildRequestListQueryParams } from "./requestsApi";

describe("buildRequestListQueryParams", () => {
  it("monta type_code, status, branch, page e page_size", () => {
    const qs = buildRequestListQueryParams({
      page: 2,
      pageSize: 20,
      typeCode: "invoice-issuance",
      status: "submitted",
      branch: "01",
    });
    const params = new URLSearchParams(qs);
    expect(params.get("page")).toBe("2");
    expect(params.get("page_size")).toBe("20");
    expect(params.get("type_code")).toBe("invoice-issuance");
    expect(params.get("status")).toBe("submitted");
    expect(params.get("branch")).toBe("01");
  });

  it("omite filtros vazios", () => {
    const qs = buildRequestListQueryParams({
      page: 1,
      pageSize: 20,
      typeCode: "  ",
      status: "",
      branch: undefined,
    });
    const params = new URLSearchParams(qs);
    expect(params.get("page")).toBe("1");
    expect(params.get("page_size")).toBe("20");
    expect(params.has("type_code")).toBe(false);
    expect(params.has("status")).toBe(false);
    expect(params.has("branch")).toBe(false);
  });
});
