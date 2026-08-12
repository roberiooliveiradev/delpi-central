import {
  buildCustomerDetailPath,
  buildAnalyticsOpportunityDetailPath,
  buildAnalyticsOtdLinePath,
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  buildPluginPath,
  buildProposalDetailPath,
  normalizePathname,
  type PluginNavigationTarget,
} from "./pluginRoutes";
import {
  sanitizeCustomersListSearch,
  type CustomersListSellerAccess,
} from "../utils/customersListDeepLink";

export function navigatePluginPath(
  target: string,
  options?: { replace?: boolean },
): void {
  if (typeof window === "undefined") return;

  const current = `${normalizePathname(window.location.pathname)}${window.location.search || ""}`;
  if (current === target) return;

  if (options?.replace) {
    window.history.replaceState(null, "", target);
  } else {
    window.history.pushState(null, "", target);
  }
  const popState =
    typeof PopStateEvent === "function"
      ? new PopStateEvent("popstate")
      : new Event("popstate");
  window.dispatchEvent(popState);
}

export function navigatePluginView(
  view: PluginNavigationTarget,
  options?: { basePath?: string; search?: string },
): void {
  const target = buildPluginPath(view, options?.basePath, options?.search);
  navigatePluginPath(target);
}

export function navigateCustomerDetail(
  codigo: string,
  loja: string,
  options?: {
    basePath?: string;
    search?: string;
    sellerAccess?: CustomersListSellerAccess;
  },
): boolean {
  const path = buildCustomerDetailPath(options?.basePath, codigo, loja);
  if (!path) return false;
  const sourceSearch =
    options?.search ?? (typeof window !== "undefined" ? window.location.search : "");
  const search = sanitizeCustomersListSearch(sourceSearch, options?.sellerAccess);
  navigatePluginPath(`${path}${search}`);
  return true;
}

export function navigateProposalDetail(
  propostaId: string,
  options?: { basePath?: string },
): boolean {
  const path = buildProposalDetailPath(options?.basePath, propostaId);
  if (!path) return false;
  navigatePluginPath(path);
  return true;
}

export function navigateAnalyticsOpportunityDetail(
  proposalNumber: string,
  options?: { basePath?: string; search?: string },
): boolean {
  const path = buildAnalyticsOpportunityDetailPath(
    options?.basePath,
    proposalNumber,
    options?.search,
  );
  if (!path) return false;
  navigatePluginPath(path);
  return true;
}

export function navigateAnalyticsOtdLine(
  branch: string,
  orderNumber: string,
  lineItem: string,
  options?: { basePath?: string; search?: string },
): boolean {
  const path = buildAnalyticsOtdLinePath(
    options?.basePath,
    branch,
    orderNumber,
    lineItem,
    options?.search,
  );
  if (!path) return false;
  navigatePluginPath(path);
  return true;
}

export function navigateOpenOrderOpDetail(
  branch: string,
  orderNumber: string,
  lineItem: string,
  productionOrder: string,
  options?: { basePath?: string; search?: string },
): boolean {
  const path = buildOpenOrderOpDetailPath(
    options?.basePath,
    branch,
    orderNumber,
    lineItem,
    productionOrder,
    options?.search,
  );
  if (!path) return false;
  navigatePluginPath(path);
  return true;
}

export function navigateOpenOrderLineDetail(
  branch: string,
  orderNumber: string,
  lineItem: string,
  options?: { basePath?: string; search?: string; replace?: boolean },
): boolean {
  const path = buildOpenOrderLineDetailPath(
    options?.basePath,
    branch,
    orderNumber,
    lineItem,
    options?.search,
  );
  if (!path) return false;
  navigatePluginPath(path, { replace: options?.replace });
  return true;
}

export {
  buildCustomerDetailPath,
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  buildProposalDetailPath,
};
