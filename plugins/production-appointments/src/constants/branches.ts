export type BranchRouteCode = "SC" | "ES";

export const DEFAULT_BRANCH_ROUTE: BranchRouteCode = "SC";

export const PRODUCTION_APPOINTMENTS_BASE_PATH = "/apps/production-appointments";

export const BRANCH_ROUTE_LABELS: Record<BranchRouteCode, string> = {
  SC: "SC",
  ES: "ES",
};

/** Código TOTVS (`H6_FILIAL`) — SC = 01, ES = 02. */
export const TOTVS_BRANCH_BY_ROUTE: Record<BranchRouteCode, string> = {
  SC: "01",
  ES: "02",
};

export function branchRouteFromPathname(pathname?: string): BranchRouteCode {
  if (!pathname) return DEFAULT_BRANCH_ROUTE;

  const normalized = pathname.toLowerCase();
  if (normalized.includes("/es")) return "ES";
  if (normalized.includes("/sc")) return "SC";

  return DEFAULT_BRANCH_ROUTE;
}

export function totvsBranchFromRoute(route: BranchRouteCode): string {
  return TOTVS_BRANCH_BY_ROUTE[route];
}
