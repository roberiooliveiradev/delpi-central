import { PRODUCTION_BASE_PATH, PRODUCTION_ROUTES } from "../constants/routes";
import type { ProductionOrderProductType } from "../types/production";
import type { ProductionFilterUrlState } from "./filterUrl";
import { appendFiltersToPath, readProductionFilters } from "./filterUrl";
import { normalizeOperationalUnitCode } from "./operationalUnitLabels";

export type ProductionView =
  | "home"
  | "oee"
  | "oee-detail"
  | "otd"
  | "otd-detail";

export type ParsedProductionRoute = {
  view: ProductionView;
  productionOrder?: string;
  appointmentId?: string;
};

export function normalizeProductionPath(pathname: string): string {
  if (!pathname) return PRODUCTION_ROUTES.home;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parseProductionPath(pathname: string): ParsedProductionRoute {
  const path = normalizeProductionPath(pathname);

  const appointmentMatch = path.match(
    new RegExp(
      `^${PRODUCTION_BASE_PATH.replace(/\//g, "\\/")}/oee/appointment/([^/]+)$`
    )
  );
  if (appointmentMatch) {
    return {
      view: "oee-detail",
      appointmentId: decodeURIComponent(appointmentMatch[1]),
    };
  }

  const orderMatch = path.match(
    new RegExp(
      `^${PRODUCTION_BASE_PATH.replace(/\//g, "\\/")}/otd/op/([^/]+)$`
    )
  );
  if (orderMatch) {
    return {
      view: "otd-detail",
      productionOrder: decodeURIComponent(orderMatch[1]),
    };
  }

  if (path === PRODUCTION_ROUTES.oee || path.startsWith(`${PRODUCTION_ROUTES.oee}/`)) {
    return { view: "oee" };
  }

  if (path === PRODUCTION_ROUTES.otd || path.startsWith(`${PRODUCTION_ROUTES.otd}/`)) {
    return { view: "otd" };
  }

  return { view: "home" };
}

export function buildOtdOrderPath(
  productionOrder: string,
  orderBranch?: string,
  filters?: ProductionFilterUrlState,
  productType?: ProductionOrderProductType
): string {
  const encoded = encodeURIComponent(productionOrder.trim());
  const basePath = `${PRODUCTION_ROUTES.otd}/op/${encoded}`;
  const resolvedFilters = filters ?? readProductionFilters();
  const params = new URLSearchParams(
    appendFiltersToPath("", resolvedFilters).replace("?", "")
  );

  if (orderBranch) {
    params.set("branch", normalizeOperationalUnitCode(orderBranch));
  }

  if (productType) {
    params.set("product_type", productType);
  }

  const query = params.toString();
  return query ? `${basePath}?${query}` : basePath;
}

export function readOrderProductTypeFromUrl(
  search = typeof window !== "undefined" ? window.location.search : ""
): ProductionOrderProductType | undefined {
  const value = new URLSearchParams(search).get("product_type")?.trim().toUpperCase();

  if (value === "PA" || value === "PI") {
    return value;
  }

  return undefined;
}

export function readAppointmentBranchFromUrl(
  search = typeof window !== "undefined" ? window.location.search : ""
): string {
  return normalizeOperationalUnitCode(
    new URLSearchParams(search).get("branch")?.trim() ?? "",
  );
}

export function readOrderBranchFromUrl(
  search = typeof window !== "undefined" ? window.location.search : ""
): string {
  return normalizeOperationalUnitCode(
    new URLSearchParams(search).get("branch")?.trim() ?? "",
  );
}
