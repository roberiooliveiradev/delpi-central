import {
  buildCustomerDetailPath,
  buildCustomerOrderDetailPath,
  buildAnalyticsOpportunityDetailPath,
  buildAnalyticsOtdLinePath,
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  buildPluginPath,
  buildProposalDetailPath,
  buildUserProfilePath,
  normalizePathname,
  type PluginNavigationTarget,
} from "./pluginRoutes";
import {
  buildHrefWithReturn,
  type ReturnNavOptions,
} from "./commercialNavigationReturn";
import {
  sanitizeCustomersListSearch,
  type CustomersListSellerAccess,
} from "../utils/customersListDeepLink";
import {
  buildCustomerDetailSearch,
  type CustomerDetailSection,
} from "../features/customers/utils/customerDetailSection";

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
  options?: { basePath?: string; search?: string; replace?: boolean },
): void {
  const target = buildPluginPath(view, options?.basePath, options?.search);
  navigatePluginPath(target, { replace: options?.replace });
}

export function navigateCustomerDetail(
  codigo: string,
  loja: string,
  options?: {
    basePath?: string;
    search?: string;
    sellerAccess?: CustomersListSellerAccess;
    /** Abre a Conta já na seção (ex.: contatos). Preserva query allowlisted da lista. */
    section?: CustomerDetailSection;
  },
): boolean {
  const path = buildCustomerDetailPath(options?.basePath, codigo, loja);
  if (!path) return false;
  const sourceSearch =
    options?.search ?? (typeof window !== "undefined" ? window.location.search : "");
  const listSearch = sanitizeCustomersListSearch(sourceSearch, options?.sellerAccess);
  const search = options?.section
    ? buildCustomerDetailSearch(options.section, listSearch)
    : listSearch;
  navigatePluginPath(`${path}${search}`);
  return true;
}

export function navigateCustomerOrderDetail(
  codigo: string,
  loja: string,
  branch: string,
  orderNumber: string,
  options?: {
    basePath?: string;
    returnNav?: ReturnNavOptions;
  },
): boolean {
  const path = buildCustomerOrderDetailPath(
    options?.basePath,
    codigo,
    loja,
    branch,
    orderNumber,
  );
  if (!path) return false;
  const target = options?.returnNav
    ? buildHrefWithReturn(path, options.returnNav, options?.basePath)
    : path;
  navigatePluginPath(target);
  return true;
}

export function navigateUserProfile(
  userId: string,
  options?: { basePath?: string; replace?: boolean },
): boolean {
  const path = buildUserProfilePath(options?.basePath, userId);
  if (!path) return false;
  navigatePluginPath(path, { replace: options?.replace });
  return true;
}

export function navigateProposalDetail(
  propostaId: string,
  options?: { basePath?: string; returnNav?: ReturnNavOptions },
): boolean {
  const path = buildProposalDetailPath(options?.basePath, propostaId);
  if (!path) return false;
  const target = options?.returnNav
    ? buildHrefWithReturn(path, options.returnNav, options?.basePath)
    : path;
  navigatePluginPath(target);
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
  options?: { basePath?: string; search?: string; returnNav?: ReturnNavOptions },
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
  const target = options?.returnNav
    ? buildHrefWithReturn(path, options.returnNav, options?.basePath)
    : path;
  navigatePluginPath(target);
  return true;
}

export function navigateOpenOrderLineDetail(
  branch: string,
  orderNumber: string,
  lineItem: string,
  options?: {
    basePath?: string;
    search?: string;
    replace?: boolean;
    returnNav?: ReturnNavOptions;
  },
): boolean {
  const path = buildOpenOrderLineDetailPath(
    options?.basePath,
    branch,
    orderNumber,
    lineItem,
    options?.search,
  );
  if (!path) return false;
  const target = options?.returnNav
    ? buildHrefWithReturn(path, options.returnNav, options?.basePath)
    : path;
  navigatePluginPath(target, { replace: options?.replace });
  return true;
}

export {
  buildCustomerDetailPath,
  buildCustomerOrderDetailPath,
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  buildProposalDetailPath,
  buildUserProfilePath,
};
