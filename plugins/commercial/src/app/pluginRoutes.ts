/** Base path canônico do plugin (manifest / Portal). */
export const COMMERCIAL_BASE_PATH = "/apps/commercial";

export type PluginView =
  | "home"
  | "my_day"
  | "open_orders"
  | "customers"
  | "customer_detail"
  | "seller_portfolios"
  | "not_found";

export type ResolvedPluginRoute = {
  view: PluginView;
  pathname: string;
  relativePath: string;
  codigo?: string;
  loja?: string;
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

export function buildPluginPath(
  view: Exclude<PluginView, "customer_detail" | "not_found">,
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

export function isPluginNavActive(
  view: PluginView,
  target: Exclude<PluginView, "customer_detail" | "not_found">,
): boolean {
  if (target === "customers") {
    return view === "customers" || view === "customer_detail";
  }
  return view === target;
}
