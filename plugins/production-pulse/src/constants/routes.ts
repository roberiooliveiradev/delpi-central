export const PRODUCTION_PULSE_BASE_PATH = "/apps/production-pulse";

export type ProductionPulseRouteKind = "panel" | "operator" | "unknown";

export type ProductionPulseRoute = {
  kind: ProductionPulseRouteKind;
};

export function parseProductionPulseRoute(pathname: string): ProductionPulseRoute {
  const normalized = pathname.replace(/\/+$/, "") || PRODUCTION_PULSE_BASE_PATH;
  if (normalized === PRODUCTION_PULSE_BASE_PATH) {
    return { kind: "panel" };
  }
  if (normalized.startsWith(`${PRODUCTION_PULSE_BASE_PATH}/operator`)) {
    return { kind: "operator" };
  }
  return { kind: "unknown" };
}
