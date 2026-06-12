import type { AccessScope, DashboardViewMode } from "../data/api/transformometroApi";

export type DashboardFilterState = {
  filialId: string;
  setorId: string;
};

export function resolveDashboardViewMode(filters: DashboardFilterState): DashboardViewMode {
  if (filters.setorId && filters.filialId) return "department";
  if (filters.filialId) return "filial";
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
    if (filters.filialId) params.filial_id = filters.filialId;
  }
  if (view === "department" && filters.setorId) {
    params.setor_id = filters.setorId;
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
