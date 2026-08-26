export const BASE_PATH = "/apps/purchase-requests";

export type PurchaseRequestsRoute = "list";

export function resolvePurchaseRequestsRoute(_pathname: string): PurchaseRequestsRoute {
  return "list";
}

export function hrefForRoute(_route: PurchaseRequestsRoute = "list"): string {
  return BASE_PATH;
}
