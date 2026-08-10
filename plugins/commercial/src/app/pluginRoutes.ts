/** Base path canônico do plugin (manifest / Portal). */
export const COMMERCIAL_BASE_PATH = "/apps/commercial";

export type PluginView =
  | "home"
  | "my_day"
  | "open_orders"
  | "open_order_op_detail"
  | "customers"
  | "customer_detail"
  | "proposals"
  | "proposal_detail"
  | "analytics"
  | "analytics_otd"
  | "analytics_otd_line"
  | "analytics_team"
  | "analytics_opportunities"
  | "analytics_opportunity_detail"
  | "seller_portfolios"
  | "not_found";

export type PluginNavId =
  | "home"
  | "my_day"
  | "open_orders"
  | "customers"
  | "proposals"
  | "analytics"
  | "seller_portfolios";

export type ResolvedPluginRoute = {
  view: PluginView;
  pathname: string;
  relativePath: string;
  codigo?: string;
  loja?: string;
  propostaId?: string;
  proposalNumber?: string;
  orderBranch?: string;
  orderNumber?: string;
  lineItem?: string;
  productionOrder?: string;
};

export function normalizePathname(pathname: string): string {
  const raw = (pathname || "").trim() || "/";
  const withoutQuery = raw.split("?")[0]?.split("#")[0] ?? raw;
  if (withoutQuery.length > 1 && withoutQuery.endsWith("/")) {
    return withoutQuery.slice(0, -1);
  }
  return withoutQuery || "/";
}

export function normalizeBasePath(basePath?: string): string {
  return normalizePathname(basePath?.trim() || COMMERCIAL_BASE_PATH);
}

function safeDecodeSegment(segment: string): string | null {
  try {
    return decodeURIComponent(segment);
  } catch {
    return null;
  }
}

export function resolvePluginRoute(
  pathname: string | undefined,
  basePath?: string,
): ResolvedPluginRoute {
  const base = normalizeBasePath(basePath);
  const path = normalizePathname(pathname ?? base);

  if (path === base) {
    return { view: "home", pathname: path, relativePath: "" };
  }

  if (!path.startsWith(`${base}/`)) {
    return { view: "not_found", pathname: path, relativePath: path };
  }

  const relativePath = path.slice(base.length + 1);

  if (relativePath === "my-day") {
    return { view: "my_day", pathname: path, relativePath };
  }

  if (relativePath === "open-orders") {
    return { view: "open_orders", pathname: path, relativePath };
  }

  const openOrderOpDetail =
    /^open-orders\/([^/]+)\/([^/]+)\/([^/]+)\/op\/([^/]+)$/.exec(relativePath);
  if (openOrderOpDetail) {
    const orderBranch = safeDecodeSegment(openOrderOpDetail[1] ?? "");
    const orderNumber = safeDecodeSegment(openOrderOpDetail[2] ?? "");
    const lineItem = safeDecodeSegment(openOrderOpDetail[3] ?? "");
    const productionOrder = safeDecodeSegment(openOrderOpDetail[4] ?? "");
    if (
      !orderBranch?.trim() ||
      !orderNumber?.trim() ||
      !lineItem?.trim() ||
      !productionOrder?.trim()
    ) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "open_order_op_detail",
      pathname: path,
      relativePath,
      orderBranch: orderBranch.trim(),
      orderNumber: orderNumber.trim(),
      lineItem: lineItem.trim(),
      productionOrder: productionOrder.trim(),
    };
  }

  if (relativePath === "customers") {
    return { view: "customers", pathname: path, relativePath };
  }

  if (relativePath === "seller-portfolios") {
    return { view: "seller_portfolios", pathname: path, relativePath };
  }

  if (relativePath === "proposals") {
    return { view: "proposals", pathname: path, relativePath };
  }

  const propostaDetail = /^proposals\/([^/]+)$/.exec(relativePath);
  if (propostaDetail) {
    const propostaId = safeDecodeSegment(propostaDetail[1] ?? "");
    if (!propostaId?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "proposal_detail",
      pathname: path,
      relativePath,
      propostaId: propostaId.trim(),
    };
  }

  if (relativePath === "analytics") {
    return { view: "analytics", pathname: path, relativePath };
  }

  if (relativePath === "analytics/otd") {
    return { view: "analytics_otd", pathname: path, relativePath };
  }

  const otdLine = /^analytics\/otd\/([^/]+)\/([^/]+)\/([^/]+)$/.exec(relativePath);
  if (otdLine) {
    const orderBranch = safeDecodeSegment(otdLine[1] ?? "");
    const orderNumber = safeDecodeSegment(otdLine[2] ?? "");
    const lineItem = safeDecodeSegment(otdLine[3] ?? "");
    if (!orderBranch?.trim() || !orderNumber?.trim() || !lineItem?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "analytics_otd_line",
      pathname: path,
      relativePath,
      orderBranch: orderBranch.trim(),
      orderNumber: orderNumber.trim(),
      lineItem: lineItem.trim(),
    };
  }

  if (relativePath === "analytics/team") {
    return { view: "analytics_team", pathname: path, relativePath };
  }

  if (relativePath === "analytics/opportunities") {
    return { view: "analytics_opportunities", pathname: path, relativePath };
  }

  const ovDetail = /^analytics\/opportunities\/([^/]+)$/.exec(relativePath);
  if (ovDetail) {
    const proposalNumber = safeDecodeSegment(ovDetail[1] ?? "");
    if (!proposalNumber?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "analytics_opportunity_detail",
      pathname: path,
      relativePath,
      proposalNumber: proposalNumber.trim(),
    };
  }


  // Legacy PT path aliases (pre-EN rename) — resolve to same views
  if (relativePath === "propostas") {
    return { view: "proposals", pathname: path, relativePath };
  }
  const legacyProposalDetail = /^propostas\/([^/]+)$/.exec(relativePath);
  if (legacyProposalDetail) {
    const propostaId = safeDecodeSegment(legacyProposalDetail[1] ?? "");
    if (!propostaId?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "proposal_detail",
      pathname: path,
      relativePath,
      propostaId: propostaId.trim(),
    };
  }
  if (relativePath === "gestao") {
    return { view: "analytics", pathname: path, relativePath };
  }
  if (relativePath === "gestao/otd") {
    return { view: "analytics_otd", pathname: path, relativePath };
  }
  if (relativePath === "gestao/equipe") {
    return { view: "analytics_team", pathname: path, relativePath };
  }
  if (relativePath === "gestao/oportunidades") {
    return { view: "analytics_opportunities", pathname: path, relativePath };
  }
  const legacyOv = /^gestao\/oportunidades\/([^/]+)$/.exec(relativePath);
  if (legacyOv) {
    const proposalNumber = safeDecodeSegment(legacyOv[1] ?? "");
    if (!proposalNumber?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "analytics_opportunity_detail",
      pathname: path,
      relativePath,
      proposalNumber: proposalNumber.trim(),
    };
  }
  const legacyOtdLine = /^gestao\/otd\/([^/]+)\/([^/]+)\/([^/]+)$/.exec(relativePath);
  if (legacyOtdLine) {
    const orderBranch = safeDecodeSegment(legacyOtdLine[1] ?? "");
    const orderNumber = safeDecodeSegment(legacyOtdLine[2] ?? "");
    const lineItem = safeDecodeSegment(legacyOtdLine[3] ?? "");
    if (!orderBranch?.trim() || !orderNumber?.trim() || !lineItem?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "analytics_otd_line",
      pathname: path,
      relativePath,
      orderBranch: orderBranch.trim(),
      orderNumber: orderNumber.trim(),
      lineItem: lineItem.trim(),
    };
  }

  const detailMatch = /^customers\/([^/]+)\/([^/]+)$/.exec(relativePath);
  if (detailMatch) {
    const rawCodigo = safeDecodeSegment(detailMatch[1] ?? "");
    const rawLoja = safeDecodeSegment(detailMatch[2] ?? "");
    if (rawCodigo === null || rawLoja === null) {
      return { view: "not_found", pathname: path, relativePath };
    }
    const codigo = rawCodigo.trim();
    const loja = rawLoja.trim();
    if (!codigo || !loja) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "customer_detail",
      pathname: path,
      relativePath,
      codigo,
      loja,
    };
  }

  return { view: "not_found", pathname: path, relativePath };
}

export type BuildablePluginView = Exclude<
  PluginView,
  | "customer_detail"
  | "open_order_op_detail"
  | "proposal_detail"
  | "analytics_otd_line"
  | "analytics_opportunity_detail"
  | "not_found"
>;

export function buildPluginPath(
  view: BuildablePluginView,
  basePath?: string,
  search?: string,
): string {
  const base = normalizeBasePath(basePath);
  const path =
    view === "open_orders"
      ? `${base}/open-orders`
      : view === "customers"
        ? `${base}/customers`
        : view === "seller_portfolios"
          ? `${base}/seller-portfolios`
          : view === "my_day"
            ? `${base}/my-day`
            : view === "proposals"
              ? `${base}/proposals`
              : view === "analytics"
                ? `${base}/analytics`
                : view === "analytics_otd"
                  ? `${base}/analytics/otd`
                  : view === "analytics_team"
                    ? `${base}/analytics/team`
                    : view === "analytics_opportunities"
                      ? `${base}/analytics/opportunities`
                      : base;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  if (normalizedSearch === "?") return path;
  return `${path}${normalizedSearch}`;
}

export function buildCustomerDetailPath(
  basePath: string | undefined,
  codigo: string,
  loja: string,
): string | null {
  const code = codigo.trim();
  const store = loja.trim();
  if (!code || !store) return null;
  const base = normalizeBasePath(basePath);
  return `${base}/customers/${encodeURIComponent(code)}/${encodeURIComponent(store)}`;
}

export function buildOpenOrderOpDetailPath(
  basePath: string | undefined,
  branch: string,
  orderNumber: string,
  lineItem: string,
  productionOrder: string,
  search?: string,
): string | null {
  const normalizedBranch = branch.trim();
  const normalizedOrder = orderNumber.trim();
  const normalizedLine = lineItem.trim();
  const normalizedOp = productionOrder.trim();
  if (!normalizedBranch || !normalizedOrder || !normalizedLine || !normalizedOp) {
    return null;
  }
  const path = `${normalizeBasePath(basePath)}/open-orders/${encodeURIComponent(normalizedBranch)}/${encodeURIComponent(normalizedOrder)}/${encodeURIComponent(normalizedLine)}/op/${encodeURIComponent(normalizedOp)}`;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  return normalizedSearch === "?" ? path : `${path}${normalizedSearch}`;
}

export function buildProposalDetailPath(
  basePath: string | undefined,
  propostaId: string,
): string | null {
  const id = propostaId.trim();
  if (!id) return null;
  return `${normalizeBasePath(basePath)}/proposals/${encodeURIComponent(id)}`;
}

export function buildAnalyticsOpportunityDetailPath(
  basePath: string | undefined,
  proposalNumber: string,
  search?: string,
): string | null {
  const number = proposalNumber.trim();
  if (!number) return null;
  const path = `${normalizeBasePath(basePath)}/analytics/opportunities/${encodeURIComponent(number)}`;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  return normalizedSearch === "?" ? path : `${path}${normalizedSearch}`;
}

export function buildAnalyticsOtdLinePath(
  basePath: string | undefined,
  branch: string,
  orderNumber: string,
  lineItem: string,
  search?: string,
): string | null {
  const b = branch.trim();
  const o = orderNumber.trim();
  const l = lineItem.trim();
  if (!b || !o || !l) return null;
  const path = `${normalizeBasePath(basePath)}/analytics/otd/${encodeURIComponent(b)}/${encodeURIComponent(o)}/${encodeURIComponent(l)}`;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  return normalizedSearch === "?" ? path : `${path}${normalizedSearch}`;
}

export function isAnalyticsView(view: PluginView): boolean {
  return (
    view === "analytics" ||
    view === "analytics_otd" ||
    view === "analytics_otd_line" ||
    view === "analytics_team" ||
    view === "analytics_opportunities" ||
    view === "analytics_opportunity_detail"
  );
}

export function resolveActiveNavId(view: PluginView): PluginNavId {
  if (view === "open_order_op_detail") return "open_orders";
  if (view === "customer_detail") return "customers";
  if (view === "proposal_detail") return "proposals";
  if (isAnalyticsView(view)) return "analytics";
  if (view === "not_found") return "home";
  if (
    view === "home" ||
    view === "my_day" ||
    view === "open_orders" ||
    view === "customers" ||
    view === "proposals" ||
    view === "seller_portfolios"
  ) {
    return view;
  }
  return "home";
}

export function isPluginNavActive(view: PluginView, target: PluginNavId): boolean {
  return resolveActiveNavId(view) === target;
}
