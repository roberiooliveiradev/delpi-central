export type ProductRouteKey =
  | "profile"
  | "guide"
  | "inspection"
  | "structure"
  | "stock"
  | "parents"
  | "analyser"
  | "other";

/** Route keys for multi-route chrome — not a display-title catalog. */
export const PRODUCT_ROUTE_KEYS: readonly ProductRouteKey[] = [
  "profile",
  "guide",
  "inspection",
  "structure",
  "stock",
  "parents",
  "analyser",
  "other",
] as const;

export function routeTitle(routeKey: ProductRouteKey): string {
  // Render-only: semântica de domínio vem da API (`resolvedRouteTitle` / `routeTitles`).
  void routeKey;
  return "Resultado";
}

export function routeFraming(routeKey: ProductRouteKey): string {
  // Sem framing de domínio local — só o que a API materializou no plan.
  void routeKey;
  return "";
}

export function isProductRouteKey(value: string): value is ProductRouteKey {
  return (PRODUCT_ROUTE_KEYS as readonly string[]).includes(value);
}
