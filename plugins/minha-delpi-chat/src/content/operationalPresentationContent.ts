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
  return presentation.routeTitles[routeKey] ?? presentation.routeTitles.other;
}

export function routeFraming(routeKey: ProductRouteKey): string {
  return presentation.routeFraming[routeKey] ?? presentation.routeFraming.other;
}

export const PRODUCT_ROUTE_KEYS = Object.keys(presentation.routeTitles) as ProductRouteKey[];

export function isProductRouteKey(value: string): value is ProductRouteKey {
  return PRODUCT_ROUTE_KEYS.includes(value as ProductRouteKey);
}
