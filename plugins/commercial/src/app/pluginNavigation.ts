import {
  buildCustomerDetailPath,
  buildCustomerOrderDetailPath,
  buildCustomerInvoiceDetailPath,
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
    returnNav?: ReturnNavOptions;
  },
): boolean {
  const target = buildCustomerDetailHref(codigo, loja, options);
  if (!target) return false;
  navigatePluginPath(target);
  return true;
}

/** Href da Conta (path + search de lista/seção + returnTo opcional). */
export function buildCustomerDetailHref(
  codigo: string,
  loja: string,
  options?: {
    basePath?: string;
    search?: string;
    sellerAccess?: CustomersListSellerAccess;
    section?: CustomerDetailSection;
    returnNav?: ReturnNavOptions;
  },
): string | null {
  const path = buildCustomerDetailPath(options?.basePath, codigo, loja);
  if (!path) return null;
  const sourceSearch =
    options?.search ?? (typeof window !== "undefined" ? window.location.search : "");
  const listSearch = sanitizeCustomersListSearch(sourceSearch, options?.sellerAccess);
  const search = options?.section
    ? buildCustomerDetailSearch(options.section, listSearch)
    : listSearch;
  const withSearch = `${path}${search}`;
  if (!options?.returnNav) return withSearch;
  return buildHrefWithReturn(withSearch, options.returnNav, options?.basePath);
}

/** Href do detalhe do pedido na Conta (+ returnTo opcional). */
export function buildCustomerOrderDetailHref(
  codigo: string,
  loja: string,
  branch: string,
  orderNumber: string,
  options?: {
    basePath?: string;
    returnNav?: ReturnNavOptions;
  },
): string | null {
  const path = buildCustomerOrderDetailPath(
    options?.basePath,
    codigo,
    loja,
    branch,
    orderNumber,
  );
  if (!path) return null;
  return options?.returnNav
    ? buildHrefWithReturn(path, options.returnNav, options?.basePath)
    : path;
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
  const target = buildCustomerOrderDetailHref(
    codigo,
    loja,
    branch,
    orderNumber,
    options,
  );
  if (!target) return false;
  navigatePluginPath(target);
  return true;
}

/** Href do detalhe da NF na Conta (+ returnTo opcional). */
export function buildCustomerInvoiceDetailHref(
  codigo: string,
  loja: string,
  branch: string,
  invoiceNumber: string,
  invoiceSeries: string,
  options?: {
    basePath?: string;
    returnNav?: ReturnNavOptions;
  },
): string | null {
  const path = buildCustomerInvoiceDetailPath(
    options?.basePath,
    codigo,
    loja,
    branch,
    invoiceNumber,
    invoiceSeries,
  );
  if (!path) return null;
  return options?.returnNav
    ? buildHrefWithReturn(path, options.returnNav, options?.basePath)
    : path;
}

export function navigateCustomerInvoiceDetail(
  codigo: string,
  loja: string,
  branch: string,
  invoiceNumber: string,
  invoiceSeries: string,
  options?: {
    basePath?: string;
    returnNav?: ReturnNavOptions;
  },
): boolean {
  const target = buildCustomerInvoiceDetailHref(
    codigo,
    loja,
    branch,
    invoiceNumber,
    invoiceSeries,
    options,
  );
  if (!target) return false;
  navigatePluginPath(target);
  return true;
}

export function navigateUserProfile(
  userId: string,
  options?: {
    basePath?: string;
    replace?: boolean;
    returnNav?: ReturnNavOptions;
  },
): boolean {
  const target = buildUserProfileHref(userId, options);
  if (!target) return false;
  navigatePluginPath(target, { replace: options?.replace });
  return true;
}

/** Href do Perfil com returnTo/returnLabel opcionais. */
export function buildUserProfileHref(
  userId: string,
  options?: { basePath?: string; returnNav?: ReturnNavOptions },
): string | null {
  const path = buildUserProfilePath(options?.basePath, userId);
  if (!path) return null;
  if (!options?.returnNav) return path;
  return buildHrefWithReturn(path, options.returnNav, options?.basePath);
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

export function buildAnalyticsOpportunityDetailHref(
  proposalNumber: string,
  options?: { basePath?: string; search?: string },
): string | null {
  return buildAnalyticsOpportunityDetailPath(
    options?.basePath,
    proposalNumber,
    options?.search,
  );
}

export function navigateAnalyticsOpportunityDetail(
  proposalNumber: string,
  options?: { basePath?: string; search?: string },
): boolean {
  const path = buildAnalyticsOpportunityDetailHref(proposalNumber, options);
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
  buildCustomerInvoiceDetailPath,
  buildAnalyticsOpportunityDetailPath,
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  buildProposalDetailPath,
  buildUserProfilePath,
  buildAnalyticsOtdLinePath,
};
