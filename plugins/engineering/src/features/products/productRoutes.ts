/** Rotas internas da feature Produtos sob `/apps/engineering/products`.
 * Caminho standalone — mesma convenção de `/nonconformities`.
 * Estado de navegação é orientado pela URL: `?tab=` na ficha e
 * `?code=&description=&groups=&types=&ref=&sort=&dir=&page=` na listagem. */

import { useEffect, useState } from "react";

export const PRODUCTS_BASE_PATH = "/apps/engineering/products";

export type ProductsView =
  | { kind: "list" }
  | { kind: "detail"; code: string }
  | { kind: "not_found" };

export const PRODUCT_PATHS = {
  list: PRODUCTS_BASE_PATH,
  detail: (code: string) =>
    `${PRODUCTS_BASE_PATH}/${encodeURIComponent(code)}`,
} as const;

// --- Abas da ficha orientadas por URL (?tab=) ---------------------------

export type ProductTabKey =
  | "overview"
  | "structure"
  | "where-used"
  | "suppliers"
  | "drawings"
  | "history";

export const PRODUCT_TAB_KEYS: readonly ProductTabKey[] = [
  "overview",
  "structure",
  "where-used",
  "suppliers",
  "drawings",
  "history",
];

/** Aceita também o identificador camelCase legado (`whereUsed`) em links
 * antigos — normaliza para o contrato kebab-case. */
const TAB_ALIASES: Record<string, ProductTabKey> = {
  overview: "overview",
  structure: "structure",
  "where-used": "where-used",
  whereUsed: "where-used",
  suppliers: "suppliers",
  drawings: "drawings",
  history: "history",
};

/** `?tab=` → aba válida; ausente/inválida → `overview` (previsível). */
export function parseProductTab(search: string): ProductTabKey {
  const raw = new URLSearchParams(search).get("tab");
  if (!raw) return "overview";
  return TAB_ALIASES[raw] ?? "overview";
}

export function productDetailTabPath(
  code: string,
  tab: ProductTabKey,
): string {
  const base = PRODUCT_PATHS.detail(code);
  return tab === "overview" ? base : `${base}?tab=${tab}`;
}

// --- Estado da listagem orientado por URL --------------------------------

export type ProductsListUrlState = {
  code: string;
  description: string;
  customer_reference: string;
  /** CSV de grupos/tipos (multiselect — contrato owner aceita lista). */
  groups: string[];
  types: string[];
  sort: string | null;
  direction: "asc" | "desc";
  page: number;
};

export const EMPTY_PRODUCTS_LIST_URL: ProductsListUrlState = {
  code: "",
  description: "",
  customer_reference: "",
  groups: [],
  types: [],
  sort: null,
  direction: "asc",
  page: 1,
};

export function parseProductsListUrl(search: string): ProductsListUrlState {
  const p = new URLSearchParams(search);
  const direction = p.get("dir") === "desc" ? "desc" : "asc";
  const page = Math.max(1, Number.parseInt(p.get("page") ?? "1", 10) || 1);
  const csv = (key: string) =>
    (p.get(key) ?? "")
      .split(",")
      .map((v) => v.trim())
      .filter(Boolean);
  return {
    code: p.get("code") ?? "",
    description: p.get("description") ?? "",
    customer_reference: p.get("ref") ?? "",
    groups: csv("groups"),
    types: csv("types"),
    sort: p.get("sort"),
    direction,
    page: Number.isFinite(page) ? page : 1,
  };
}

export function buildProductsListUrl(state: ProductsListUrlState): string {
  const p = new URLSearchParams();
  if (state.code) p.set("code", state.code);
  if (state.description) p.set("description", state.description);
  if (state.customer_reference) p.set("ref", state.customer_reference);
  if (state.groups.length) p.set("groups", state.groups.join(","));
  if (state.types.length) p.set("types", state.types.join(","));
  if (state.sort) p.set("sort", state.sort);
  if (state.direction === "desc") p.set("dir", "desc");
  if (state.page > 1) p.set("page", String(state.page));
  const query = p.toString();
  return `${PRODUCTS_BASE_PATH}${query ? `?${query}` : ""}`;
}

// --- Resolução/navegação --------------------------------------------------

export function resolveProductsPath(relativePath: string): ProductsView {
  const path = relativePath.replace(/^\/+|\/+$/g, "");
  if (path === "" || path === "products") return { kind: "list" };
  const rest = path.startsWith("products/")
    ? path.slice("products/".length)
    : path;
  const segments = rest.split("/").filter(Boolean);
  if (segments.length === 1 && segments[0]) {
    return { kind: "detail", code: decodeURIComponent(segments[0]) };
  }
  return { kind: "not_found" };
}

export function navigateProducts(
  path: string,
  options?: { replace?: boolean },
) {
  if (typeof window === "undefined") return;
  if (options?.replace) {
    window.history.replaceState(window.history.state, "", path);
  } else {
    window.history.pushState(window.history.state, "", path);
  }
  window.dispatchEvent(
    new PopStateEvent("popstate", { state: window.history.state }),
  );
}

function readLocationSearch(): string {
  if (typeof window === "undefined") return "";
  return window.location.search;
}

/** `window.location.search` reativo a navegação (popstate/back/forward)
 * — mesmo padrão de `useLmpsRouterPath`. */
export function useLocationSearch(): string {
  const [search, setSearch] = useState(readLocationSearch);
  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const sync = () => setSearch(readLocationSearch());
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);
  return search;
}
