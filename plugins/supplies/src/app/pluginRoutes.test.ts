import { describe, expect, it } from "vitest";

import { canAccessView } from "./routeAccess";
import { buildPluginPath, resolvePluginRoute } from "./pluginRoutes";

const portalOnly = {
  portal: true,
  purchaseRequests: false,
  operations: false,
  analytics: false,
  administration: false,
  viewAll: false,
  export: false,
};

describe("pluginRoutes", () => {
  it("resolves canonical english paths", () => {
    expect(resolvePluginRoute("/apps/supplies/purchase-requests").view).toBe("purchase_requests");
    expect(buildPluginPath("safety_stock")).toBe("/apps/supplies/safety-stock");
  });

  it("returns not_found for unknown paths", () => {
    expect(resolvePluginRoute("/apps/supplies/imports").view).toBe("not_found");
  });
});

describe("routeAccess", () => {
  it("allows home and blocks overview without analytics", () => {
    expect(canAccessView("home", portalOnly)).toBe(true);
    expect(canAccessView("overview", portalOnly)).toBe(false);
  });
});
