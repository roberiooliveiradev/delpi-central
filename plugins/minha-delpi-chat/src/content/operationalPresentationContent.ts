import productOperationalContent from "./product_operational_content.json";

export type ProductRouteKey =
  | "profile"
  | "guide"
  | "inspection"
  | "structure"
  | "stock"
  | "parents"
  | "analyser"
  | "other";

type PresentationContent = typeof productOperationalContent.presentation;

const presentation = productOperationalContent.presentation as PresentationContent;

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

export const PRODUCT_ROUTE_KEYS = Object.keys(presentation.routeTitles) as ProductRouteKey[];

export function isProductRouteKey(value: string): value is ProductRouteKey {
  return PRODUCT_ROUTE_KEYS.includes(value as ProductRouteKey);
}
