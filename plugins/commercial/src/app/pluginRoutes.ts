/** Base path canônico do plugin (manifest / Portal). */
export const COMMERCIAL_BASE_PATH = "/apps/commercial";

export type PluginView =
  | "home"
  | "my_day"
  | "open_orders"
  | "customers"
  | "customer_detail"
  | "propostas"
  | "proposta_detail"
  | "gestao"
  | "gestao_otd"
  | "gestao_otd_line"
  | "gestao_equipe"
  | "gestao_oportunidades"
  | "gestao_oportunidade_detail"
  | "seller_portfolios"
  | "not_found";

export type PluginNavId =
  | "home"
  | "my_day"
  | "open_orders"
  | "customers"
  | "propostas"
  | "gestao"
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

  if (relativePath === "customers") {
    return { view: "customers", pathname: path, relativePath };
  }

  if (relativePath === "seller-portfolios") {
    return { view: "seller_portfolios", pathname: path, relativePath };
  }

  if (relativePath === "propostas") {
    return { view: "propostas", pathname: path, relativePath };
  }

  const propostaDetail = /^propostas\/([^/]+)$/.exec(relativePath);
  if (propostaDetail) {
    const propostaId = safeDecodeSegment(propostaDetail[1] ?? "");
    if (!propostaId?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "proposta_detail",
      pathname: path,
      relativePath,
      propostaId: propostaId.trim(),
    };
  }

  if (relativePath === "gestao") {
    return { view: "gestao", pathname: path, relativePath };
  }

  if (relativePath === "gestao/otd") {
    return { view: "gestao_otd", pathname: path, relativePath };
  }

  const otdLine = /^gestao\/otd\/([^/]+)\/([^/]+)\/([^/]+)$/.exec(relativePath);
  if (otdLine) {
    const orderBranch = safeDecodeSegment(otdLine[1] ?? "");
    const orderNumber = safeDecodeSegment(otdLine[2] ?? "");
    const lineItem = safeDecodeSegment(otdLine[3] ?? "");
    if (!orderBranch?.trim() || !orderNumber?.trim() || !lineItem?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "gestao_otd_line",
      pathname: path,
      relativePath,
      orderBranch: orderBranch.trim(),
      orderNumber: orderNumber.trim(),
      lineItem: lineItem.trim(),
    };
  }

  if (relativePath === "gestao/equipe") {
    return { view: "gestao_equipe", pathname: path, relativePath };
  }

  if (relativePath === "gestao/oportunidades") {
    return { view: "gestao_oportunidades", pathname: path, relativePath };
  }

  const ovDetail = /^gestao\/oportunidades\/([^/]+)$/.exec(relativePath);
  if (ovDetail) {
    const proposalNumber = safeDecodeSegment(ovDetail[1] ?? "");
    if (!proposalNumber?.trim()) {
      return { view: "not_found", pathname: path, relativePath };
    }
    return {
      view: "gestao_oportunidade_detail",
      pathname: path,
      relativePath,
      proposalNumber: proposalNumber.trim(),
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
  | "proposta_detail"
  | "gestao_otd_line"
  | "gestao_oportunidade_detail"
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
            : view === "propostas"
              ? `${base}/propostas`
              : view === "gestao"
                ? `${base}/gestao`
                : view === "gestao_otd"
                  ? `${base}/gestao/otd`
                  : view === "gestao_equipe"
                    ? `${base}/gestao/equipe`
                    : view === "gestao_oportunidades"
                      ? `${base}/gestao/oportunidades`
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

export function buildPropostaDetailPath(
  basePath: string | undefined,
  propostaId: string,
): string | null {
  const id = propostaId.trim();
  if (!id) return null;
  return `${normalizeBasePath(basePath)}/propostas/${encodeURIComponent(id)}`;
}

export function buildGestaoOportunidadeDetailPath(
  basePath: string | undefined,
  proposalNumber: string,
  search?: string,
): string | null {
  const number = proposalNumber.trim();
  if (!number) return null;
  const path = `${normalizeBasePath(basePath)}/gestao/oportunidades/${encodeURIComponent(number)}`;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  return normalizedSearch === "?" ? path : `${path}${normalizedSearch}`;
}

export function buildGestaoOtdLinePath(
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
  const path = `${normalizeBasePath(basePath)}/gestao/otd/${encodeURIComponent(b)}/${encodeURIComponent(o)}/${encodeURIComponent(l)}`;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  return normalizedSearch === "?" ? path : `${path}${normalizedSearch}`;
}

export function isGestaoView(view: PluginView): boolean {
  return (
    view === "gestao" ||
    view === "gestao_otd" ||
    view === "gestao_otd_line" ||
    view === "gestao_equipe" ||
    view === "gestao_oportunidades" ||
    view === "gestao_oportunidade_detail"
  );
}

export function resolveActiveNavId(view: PluginView): PluginNavId {
  if (view === "customer_detail") return "customers";
  if (view === "proposta_detail") return "propostas";
  if (isGestaoView(view)) return "gestao";
  if (view === "not_found") return "home";
  if (
    view === "home" ||
    view === "my_day" ||
    view === "open_orders" ||
    view === "customers" ||
    view === "propostas" ||
    view === "seller_portfolios"
  ) {
    return view;
  }
  return "home";
}

export function isPluginNavActive(view: PluginView, target: PluginNavId): boolean {
  return resolveActiveNavId(view) === target;
}
