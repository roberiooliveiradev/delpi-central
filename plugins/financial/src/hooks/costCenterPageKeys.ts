/** Filtros mínimos para as chaves de cache da lista de despesas por CC. */
export type CostCenterPageKeyFilters = {
  branch: string;
  startDate: string | null;
  endDate: string | null;
  costCenter: string | null;
  supplierCode: string | null;
  supplierStore: string | null;
  excludeMp: boolean;
  search: string | null;
  page: number;
  sortBy: string;
  sortDir: "asc" | "desc";
};

/** Escopo do painel (filtros/KPIs/série/rankings) — sem página/ordenação/busca. */
export function costCenterPageDashboardKey(
  filters: Pick<
    CostCenterPageKeyFilters,
    | "branch"
    | "startDate"
    | "endDate"
    | "costCenter"
    | "supplierCode"
    | "supplierStore"
    | "excludeMp"
  >,
): string {
  return [
    filters.branch,
    filters.startDate,
    filters.endDate,
    filters.costCenter,
    filters.supplierCode,
    filters.supplierStore,
    filters.excludeMp,
  ].join("|");
}

/** Escopo só dos lançamentos paginados. */
export function costCenterPageEntriesKey(filters: CostCenterPageKeyFilters): string {
  return [
    costCenterPageDashboardKey(filters),
    filters.search,
    filters.page,
    filters.sortBy,
    filters.sortDir,
  ].join("|");
}
