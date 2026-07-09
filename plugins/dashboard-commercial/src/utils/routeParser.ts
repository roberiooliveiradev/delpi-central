import { COMMERCIAL_BASE_PATH, COMMERCIAL_ROUTES } from "../constants/routes";
import { normalizeOperationalUnitCode } from "./operationalUnitLabels";
import type { CommercialFilterUrlState } from "./filterUrl";
import { appendFiltersToPath } from "./filterUrl";

export type CommercialView = "dashboard" | "ov-detail" | "sales-order-otd" | "sales-order-otd-detail";

export type ParsedCommercialRoute = {
  view: CommercialView;
  proposalNumber?: string;
  orderBranch?: string;
  orderNumber?: string;
  lineItem?: string;
};

export function normalizeCommercialPath(pathname: string): string {
  if (!pathname) return COMMERCIAL_BASE_PATH;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parseCommercialPath(pathname: string): ParsedCommercialRoute {
  const path = normalizeCommercialPath(pathname);
  const base = COMMERCIAL_BASE_PATH.replace(/\//g, "\\/");

  const otdDetailMatch = path.match(
    new RegExp(`^${base}/otd/pedido/([^/]+)/([^/]+)/([^/]+)$`, "i"),
  );
  if (otdDetailMatch) {
    return {
      view: "sales-order-otd-detail",
      orderBranch: decodeURIComponent(otdDetailMatch[1]),
      orderNumber: decodeURIComponent(otdDetailMatch[2]),
      lineItem: decodeURIComponent(otdDetailMatch[3]),
    };
  }

  if (path === COMMERCIAL_ROUTES.salesOrderOtd) {
    return { view: "sales-order-otd" };
  }

  const ovMatch = path.match(new RegExp(`^${base}/ov/([^/]+)$`, "i"));
  if (ovMatch) {
    return {
      view: "ov-detail",
      proposalNumber: decodeURIComponent(ovMatch[1]),
    };
  }

  return { view: "dashboard" };
}

export function buildSalesOrderOtdLinePath(
  branch: string,
  orderNumber: string,
  lineItem: string,
  state: CommercialFilterUrlState,
): string {
  const encodedBranch = encodeURIComponent(normalizeOperationalUnitCode(branch));
  const encodedOrder = encodeURIComponent(String(orderNumber).trim());
  const encodedLine = encodeURIComponent(String(lineItem).trim());
  return appendFiltersToPath(
    `${COMMERCIAL_ROUTES.salesOrderOtd}/pedido/${encodedBranch}/${encodedOrder}/${encodedLine}`,
    state,
  );
}

export function readProposalBranchFromUrl(
  search = typeof window !== "undefined" ? window.location.search : "",
): string | undefined {
  const value = new URLSearchParams(search).get("branch")?.trim();
  const normalized = normalizeOperationalUnitCode(value);
  return normalized || undefined;
}

export function readProposalRevisionFromUrl(
  search = typeof window !== "undefined" ? window.location.search : "",
): string | undefined {
  const value = new URLSearchParams(search).get("revision")?.trim();
  return value || undefined;
}
