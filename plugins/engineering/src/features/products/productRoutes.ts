/** Rotas internas da feature Produtos sob `/apps/engineering/products`.
 * Caminho standalone — mesma convenção de `/nonconformities`. */

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
