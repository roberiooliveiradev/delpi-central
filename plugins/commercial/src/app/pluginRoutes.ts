/** Base path canônico do plugin (manifest / Portal). */
export const COMMERCIAL_BASE_PATH = "/apps/commercial";

export type PluginView =
  | "home"
  | "overview"
  | "my_tasks"
  | "open_orders"
  | "open_order_line_detail"
  | "open_order_op_detail"
  | "customers"
  | "customer_detail"
  | "proposals"
  | "proposal_detail"
  | "analytics_otd"
  | "analytics_otd_line"
  | "analytics_team"
  | "analytics_opportunities"
  | "analytics_opportunity_detail"
  | "administration"
  | "administration_portfolios"
  | "administration_members"
  | "seller_portfolios"
  | "seller_portfolio_detail"
  | "user_profile"
  | "not_found";

/** Itens da navegação de topo (IA 2026 — seis áreas). */
export type PluginNavId =
  | "home"
  | "overview"
  | "my_tasks"
  | "open_orders"
  | "customers"
  | "administration";

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
  portfolioId?: string;
  userId?: string;
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

  if (relativePath === "my-tasks" || relativePath === "my-day") {
    return { view: "my_tasks", pathname: path, relativePath };
  }

  const userProfile = /^users\/([^/]+)$/.exec(relativePath);
  if (userProfile) {
    const userId = safeDecodeSegment(userProfile[1] ?? "");
    if (!userId?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "user_profile",
      pathname: path,
      relativePath,
      userId: userId.trim(),
    };
  }

  if (relativePath === "overview") {
    return { view: "overview", pathname: path, relativePath };
  }

  if (relativePath === "open-orders") {
    return { view: "open_orders", pathname: path, relativePath };
  }

  const openOrderLineDetail =
    /^open-orders\/([^/]+)\/([^/]+)\/([^/]+)$/.exec(relativePath);
  if (openOrderLineDetail) {
    const orderBranch = safeDecodeSegment(openOrderLineDetail[1] ?? "");
    const orderNumber = safeDecodeSegment(openOrderLineDetail[2] ?? "");
    const lineItem = safeDecodeSegment(openOrderLineDetail[3] ?? "");
    if (!orderBranch?.trim() || !orderNumber?.trim() || !lineItem?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "open_order_line_detail",
      pathname: path,
      relativePath,
      orderBranch: orderBranch.trim(),
      orderNumber: orderNumber.trim(),
      lineItem: lineItem.trim(),
    };
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

  if (relativePath === "administration") {
    return { view: "administration", pathname: path, relativePath };
  }

  if (relativePath === "administration/seller-portfolios") {
    return { view: "administration_portfolios", pathname: path, relativePath };
  }

  // Canônico `/administration/team`; alias `/administration/members`.
  if (relativePath === "administration/team" || relativePath === "administration/members") {
    return { view: "administration_members", pathname: path, relativePath };
  }

  const adminPortfolioDetail = /^administration\/seller-portfolios\/([^/]+)$/.exec(relativePath);
  if (adminPortfolioDetail) {
    const portfolioId = safeDecodeSegment(adminPortfolioDetail[1] ?? "");
    if (!portfolioId?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "seller_portfolio_detail",
      pathname: path,
      relativePath,
      portfolioId: portfolioId.trim(),
    };
  }

  // Alias legado: lista e detalhe flat sob `/seller-portfolios`.
  if (relativePath === "seller-portfolios") {
    return { view: "administration_portfolios", pathname: path, relativePath };
  }

  const sellerPortfolioDetail = /^seller-portfolios\/([^/]+)$/.exec(relativePath);
  if (sellerPortfolioDetail) {
    const portfolioId = safeDecodeSegment(sellerPortfolioDetail[1] ?? "");
    if (!portfolioId?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "seller_portfolio_detail",
      pathname: path,
      relativePath,
      portfolioId: portfolioId.trim(),
    };
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

  // `/analytics` continua válido como caminho legado da Visão geral.
  if (relativePath === "analytics") {
    return { view: "overview", pathname: path, relativePath };
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
    return { view: "overview", pathname: path, relativePath };
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
  | "open_order_line_detail"
  | "open_order_op_detail"
  | "proposal_detail"
  | "analytics_otd_line"
  | "analytics_opportunity_detail"
  | "seller_portfolio_detail"
  | "user_profile"
  | "not_found"
>;

/**
 * Vocabulário de navegação da arquitetura de informação 2026 (Início launcher,
 * Visão geral, Minhas tarefas, Administração).
 */
export type PluginNavigationTarget = BuildablePluginView;

const PLUGIN_VIEW_RELATIVE_PATHS: Record<BuildablePluginView, string> = {
  home: "",
  overview: "overview",
  my_tasks: "my-tasks",
  open_orders: "open-orders",
  customers: "customers",
  proposals: "proposals",
  analytics_otd: "analytics/otd",
  analytics_team: "analytics/team",
  analytics_opportunities: "analytics/opportunities",
  administration: "administration",
  administration_portfolios: "administration/seller-portfolios",
  administration_members: "administration/team",
  /** Alias legado — resolve para a aba Carteiras do hub. */
  seller_portfolios: "administration/seller-portfolios",
};

export function buildPluginPath(
  view: PluginNavigationTarget,
  basePath?: string,
  search?: string,
): string {
  const base = normalizeBasePath(basePath);
  const relative = PLUGIN_VIEW_RELATIVE_PATHS[view] ?? "";
  const path = relative ? `${base}/${relative}` : base;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  if (normalizedSearch === "?") return path;
  return `${path}${normalizedSearch}`;
}

export function buildSellerPortfolioDetailPath(
  basePath: string | undefined,
  portfolioId: string,
  search?: string,
): string | null {
  const id = portfolioId.trim();
  if (!id) return null;
  const path = `${normalizeBasePath(basePath)}/administration/seller-portfolios/${encodeURIComponent(id)}`;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  return normalizedSearch === "?" ? path : `${path}${normalizedSearch}`;
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

export function buildUserProfilePath(
  basePath: string | undefined,
  userId: string,
): string | null {
  const id = userId.trim();
  if (!id) return null;
  return `${normalizeBasePath(basePath)}/users/${encodeURIComponent(id)}`;
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

export function buildOpenOrderLineDetailPath(
  basePath: string | undefined,
  branch: string,
  orderNumber: string,
  lineItem: string,
  search?: string,
): string | null {
  const normalizedBranch = branch.trim();
  const normalizedOrder = orderNumber.trim();
  const normalizedLine = lineItem.trim();
  if (!normalizedBranch || !normalizedOrder || !normalizedLine) return null;
  const path = `${normalizeBasePath(basePath)}/open-orders/${encodeURIComponent(normalizedBranch)}/${encodeURIComponent(normalizedOrder)}/${encodeURIComponent(normalizedLine)}`;
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

/** Páginas de diagnóstico profundo (drill da Visão geral), fora da navegação de topo. */
export function isAnalyticsDeepView(view: PluginView): boolean {
  return (
    view === "analytics_otd" ||
    view === "analytics_otd_line" ||
    view === "analytics_team" ||
    view === "analytics_opportunities" ||
    view === "analytics_opportunity_detail"
  );
}

/**
 * Item de topo destacado para a view atual. Páginas profundas (OTD, oportunidades,
 * equipe, propostas) não pertencem à navegação de topo e ficam sem destaque.
 */
export function resolveActiveNavId(view: PluginView): PluginNavId | null {
  if (view === "open_order_line_detail" || view === "open_order_op_detail") return "open_orders";
  if (view === "customer_detail") return "customers";
  if (
    view === "administration" ||
    view === "administration_portfolios" ||
    view === "administration_members" ||
    view === "seller_portfolios" ||
    view === "seller_portfolio_detail"
  ) {
    return "administration";
  }
  if (view === "proposals" || view === "proposal_detail") return null;
  if (view === "user_profile") return null;
  if (isAnalyticsDeepView(view)) return null;
  if (view === "not_found") return "home";
  if (
    view === "home" ||
    view === "overview" ||
    view === "my_tasks" ||
    view === "open_orders" ||
    view === "customers"
  ) {
    return view;
  }
  return "home";
}

export function isPluginNavActive(view: PluginView, target: PluginNavId): boolean {
  return resolveActiveNavId(view) === target;
}
