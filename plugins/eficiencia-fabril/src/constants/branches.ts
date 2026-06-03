export type BranchRouteCode = "SC" | "ES";

export const BRANCH_ROUTE_LABELS: Record<BranchRouteCode, string> = {
  SC: "Filial SC",
  ES: "Filial ES",
};

/** Código TOTVS (`FILIAL`) na view — SC = 01, ES = 02. */
export const TOTVS_BRANCH_BY_ROUTE: Record<BranchRouteCode, string> = {
  SC: "01",
  ES: "02",
};

export function branchRouteFromPathname(pathname?: string): BranchRouteCode | null {
  if (!pathname) return null;

  const normalized = pathname.toLowerCase();
  if (normalized.includes("/sc")) return "SC";
  if (normalized.includes("/es")) return "ES";
  return null;
}

export function totvsBranchFromRoute(route: BranchRouteCode): string {
  return TOTVS_BRANCH_BY_ROUTE[route];
}

export function viewPermissionForBranch(route: BranchRouteCode): string {
  return `eficiencia-fabril.view.filial-${route.toLowerCase()}`;
}
