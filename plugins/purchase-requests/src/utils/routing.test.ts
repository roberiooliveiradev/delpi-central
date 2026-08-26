import { describe, expect, it } from "vitest";

import { BASE_PATH, hrefForRoute, resolvePurchaseRequestsRoute } from "./routing";

describe("routing", () => {
  it("resolves every path as the list route", () => {
    expect(resolvePurchaseRequestsRoute(BASE_PATH)).toBe("list");
    expect(resolvePurchaseRequestsRoute(`${BASE_PATH}/`)).toBe("list");
    expect(resolvePurchaseRequestsRoute(`${BASE_PATH}/admin`)).toBe("list");
  });

  it("builds hrefs for the list route", () => {
    expect(hrefForRoute("list")).toBe(BASE_PATH);
  });
});
