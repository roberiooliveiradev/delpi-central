import type { AccessScope, DashboardViewMode } from "../data/api/transformometroApi";

export type DashboardFilterState = {
  filialIds: string[];
  setorIds: string[];
};

export function resolveDashboardViewMode(filters: DashboardFilterState): DashboardViewMode {
  if (filters.setorIds.length > 0 && filters.filialIds.length > 0) return "department";
  if (filters.filialIds.length > 0) return "filial";
  return "consolidated";
}

export function buildDashboardQueryParams(
  filters: DashboardFilterState & { dataInicial?: string; dataFinal?: string },
  accessScope?: AccessScope | null
): Record<string, string> {
  const params: Record<string, string> = {};
  if (filters.dataInicial) params.competencia_inicio = filters.dataInicial;
  if (filters.dataFinal) params.competencia_fim = filters.dataFinal;

  const view = resolveDashboardViewMode(filters);
  params.view = view;

  if (view === "filial" || view === "department") {
    if (filters.filialIds.length > 0) params.filial_id = filters.filialIds.join(",");
  }
  if (view === "department" && filters.setorIds.length > 0) {
    params.setor_id = filters.setorIds.join(",");
  }

  if (accessScope?.mode === "scoped" && view === "consolidated" && !accessScope.can_view_consolidated) {
    const fallback = accessScope.allowed_filiais[0];
    if (fallback) {
      params.view = "filial";
      params.filial_id = fallback;
    }
  }

  return params;
}

export function canSelectConsolidatedView(accessScope?: AccessScope | null): boolean {
  if (!accessScope || accessScope.mode !== "scoped") return true;
  return accessScope.can_view_consolidated;
}

export function defaultDashboardFilialFilter(accessScope?: AccessScope | null): string {
  if (!accessScope || accessScope.mode !== "scoped") return "";
  if (accessScope.can_view_consolidated) return "";
  return accessScope.allowed_filiais[0] ?? "";
}
