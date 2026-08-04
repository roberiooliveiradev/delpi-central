/** Base path canônico do plugin (manifest / Portal). */
export const PVA_BASE_PATH = "/apps/pedidos-venda-abertos";

export type PluginView =
  | "orders"
  | "customers"
  | "customer_detail"
  | "config"
  | "not_found";

export type ResolvedPluginRoute = {
  view: PluginView;
  /** Pathname normalizado (sem barra final, sem query). */
  pathname: string;
  /** Path relativo ao basePath ("" | "clientes" | …). */
  relativePath: string;
  /** Presente quando view === "customer_detail". */
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
  return normalizePathname(basePath?.trim() || PVA_BASE_PATH);
}

function safeDecodeSegment(segment: string): string | null {
  try {
    return decodeURIComponent(segment);
  } catch {
    return null;
  }
}

/**
 * Resolve a view interna a partir do pathname do Portal / browser.
 * Query string deve ser removida antes (via normalizePathname).
 */
export function resolvePluginRoute(
  pathname: string | undefined,
  basePath?: string,
): ResolvedPluginRoute {
  const base = normalizeBasePath(basePath);
  const path = normalizePathname(pathname ?? base);

  if (path === base) {
    return { view: "orders", pathname: path, relativePath: "" };
  }

  if (!path.startsWith(`${base}/`)) {
    return { view: "not_found", pathname: path, relativePath: path };
  }

  const relativePath = path.slice(base.length + 1);

  if (relativePath === "clientes") {
    return { view: "customers", pathname: path, relativePath };
  }

  if (relativePath === "configuracao") {
    return { view: "config", pathname: path, relativePath };
  }

  const detailMatch = /^clientes\/([^/]+)\/([^/]+)$/.exec(relativePath);
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
  view: "orders" | "customers" | "config",
  basePath?: string,
  search?: string,
): string {
  const base = normalizeBasePath(basePath);
  const path =
    view === "customers"
      ? `${base}/clientes`
      : view === "config"
        ? `${base}/configuracao`
        : base;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  if (normalizedSearch === "?") return path;
  return `${path}${normalizedSearch}`;
}

/**
 * Aba Clientes permanece ativa também no detalhe individual.
 */
export function isPluginNavActive(
  view: PluginView,
  target: "orders" | "customers" | "config",
): boolean {
  if (target === "customers") {
    return view === "customers" || view === "customer_detail";
  }
  return view === target;
}
