import { describe, expect, it } from "vitest";

import { canAccessView } from "./routeAccess";
import { buildPluginPath, buildPurchaseOrderDetailPath, resolvePluginRoute } from "./pluginRoutes";

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
    expect(resolvePluginRoute("/apps/supplies/analytics/otd").view).toBe("analytics_otd");
    const detail = resolvePluginRoute("/apps/supplies/purchase-orders/01/000123");
    expect(detail.view).toBe("purchase_order_detail");
    expect(detail.branch).toBe("01");
    expect(detail.orderNumber).toBe("000123");
    expect(buildPurchaseOrderDetailPath("01", "000123")).toBe(
      "/apps/supplies/purchase-orders/01/000123",
    );
    expect(buildPluginPath("safety_stock")).toBe("/apps/supplies/safety-stock");
    expect(buildPluginPath("analytics_otd")).toBe("/apps/supplies/analytics/otd");
  });

  it("returns not_found for unknown paths", () => {
    expect(resolvePluginRoute("/apps/supplies/imports").view).toBe("not_found");
    expect(resolvePluginRoute("/apps/supplies/purchase-orders/01").view).toBe("not_found");
  });
});

describe("routeAccess", () => {
  it("allows home and blocks overview without analytics", () => {
    expect(canAccessView("home", portalOnly)).toBe(true);
    expect(canAccessView("overview", portalOnly)).toBe(false);
  });

  it("exige operations para lista e ficha de pedidos", () => {
    expect(canAccessView("purchase_orders", portalOnly)).toBe(false);
    expect(canAccessView("purchase_order_detail", portalOnly)).toBe(false);
    expect(
      canAccessView("purchase_order_detail", { ...portalOnly, operations: true }),
    ).toBe(true);
  });
});
