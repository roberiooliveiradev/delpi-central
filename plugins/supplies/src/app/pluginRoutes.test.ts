import { describe, expect, it } from "vitest";

import { canAccessView } from "./routeAccess";
import {
  buildPluginPath,
  buildPurchaseOrderDetailPath,
  buildPurchaseRequestDetailPath,
  buildSafetyStockDetailPath,
  resolveActiveNavId,
  resolvePluginRoute,
} from "./pluginRoutes";

const noAccess = {
  access: false,
  manage: false,
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

  it("resolves purchase request detail direct URL and encoded segments", () => {
    const detail = resolvePluginRoute("/apps/supplies/purchase-requests/01/177416");
    expect(detail.view).toBe("purchase_request_detail");
    expect(detail.branch).toBe("01");
    expect(detail.requestNumber).toBe("177416");
    expect(buildPurchaseRequestDetailPath("01", "177416")).toBe(
      "/apps/supplies/purchase-requests/01/177416",
    );

    const encoded = resolvePluginRoute(
      "/apps/supplies/purchase-requests/01/177%20416",
    );
    expect(encoded.view).toBe("purchase_request_detail");
    expect(encoded.branch).toBe("01");
    expect(encoded.requestNumber).toBe("177 416");

    expect(resolveActiveNavId("purchase_request_detail")).toBe("purchase_requests");
    expect(resolveActiveNavId("purchase_requests")).toBe("purchase_requests");
  });

  it("resolves safety stock detail path, encodes segments and nav", () => {
    const detail = resolvePluginRoute("/apps/supplies/safety-stock/01/00100708");
    expect(detail.view).toBe("safety_stock_detail");
    expect(detail.branch).toBe("01");
    expect(detail.productCode).toBe("00100708");

    const sibling = resolvePluginRoute("/apps/supplies/safety-stock/02/ABC");
    expect(sibling.view).toBe("safety_stock_detail");
    expect(sibling.branch).toBe("02");
    expect(sibling.productCode).toBe("ABC");

    // `all` resolve a rota — a página decide o estado de filial inválida.
    expect(resolvePluginRoute("/apps/supplies/safety-stock/all/ABC").view).toBe(
      "safety_stock_detail",
    );

    const encoded = resolvePluginRoute(
      "/apps/supplies/safety-stock/01/A%20B",
    );
    expect(encoded.productCode).toBe("A B");

    expect(buildSafetyStockDetailPath("01", "00100708")).toBe(
      "/apps/supplies/safety-stock/01/00100708",
    );
    expect(
      buildSafetyStockDetailPath("02", "A B", undefined, "?from=x"),
    ).toBe("/apps/supplies/safety-stock/02/A%20B?from=x");

    expect(resolveActiveNavId("safety_stock_detail")).toBe("operations");
    // Caminho sem filial/código continua na listagem ou em not_found.
    expect(resolvePluginRoute("/apps/supplies/safety-stock").view).toBe(
      "safety_stock",
    );
    expect(resolvePluginRoute("/apps/supplies/safety-stock/01").view).toBe(
      "not_found",
    );
  });

  it("returns not_found for unknown paths", () => {
    expect(resolvePluginRoute("/apps/supplies/imports").view).toBe("not_found");
    expect(resolvePluginRoute("/apps/supplies/purchase-orders/01").view).toBe("not_found");
    expect(resolvePluginRoute("/apps/supplies/purchase-requests/01").view).toBe("not_found");
  });
});

describe("routeAccess", () => {
  it("allows home and blocks overview without analytics", () => {
    expect(canAccessView("home", noAccess)).toBe(false);
    expect(canAccessView("overview", noAccess)).toBe(false);
  });

  it("exige operations para lista e ficha de pedidos", () => {
    expect(canAccessView("purchase_orders", noAccess)).toBe(false);
    expect(canAccessView("purchase_order_detail", noAccess)).toBe(false);
    expect(canAccessView("purchase_order_detail", { ...noAccess, access: true })).toBe(true);
  });

  it("canonical access abre uso normal e manage-only só administração", () => {
    const accessOnly = { ...noAccess, access: true };
    expect(canAccessView("purchase_orders", accessOnly)).toBe(true);
    expect(canAccessView("administration", accessOnly)).toBe(false);
    const manageOnly = { ...noAccess, manage: true };
    expect(canAccessView("administration", manageOnly)).toBe(true);
    expect(canAccessView("overview", manageOnly)).toBe(false);
    expect(canAccessView("purchase_orders", manageOnly)).toBe(false);
  });
});
