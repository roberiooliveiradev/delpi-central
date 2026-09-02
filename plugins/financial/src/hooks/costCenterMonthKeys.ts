/** Filtros mínimos para as chaves de cache do detalhe do mês. */
export type CostCenterMonthKeyFilters = {
  branch: string;
  month: string;
  costCenter: string | null;
  supplierCode: string | null;
  supplierStore: string | null;
  excludeMp: boolean;
  search: string | null;
  page: number;
  sortBy: string;
  sortDir: "asc" | "desc";
};

/** Escopo do painel (KPIs + rankings) — sem página/ordenação/busca da tabela. */
export function costCenterMonthDashboardKey(
  filters: Pick<
    CostCenterMonthKeyFilters,
    | "branch"
    | "month"
    | "costCenter"
    | "supplierCode"
    | "supplierStore"
    | "excludeMp"
  >,
): string {
  return [
    filters.branch,
    filters.month,
    filters.costCenter,
    filters.supplierCode,
    filters.supplierStore,
    filters.excludeMp,
  ].join("|");
}

/** Escopo só dos lançamentos paginados. */
export function costCenterMonthEntriesKey(filters: CostCenterMonthKeyFilters): string {
  return [
    costCenterMonthDashboardKey(filters),
    filters.search,
    filters.page,
    filters.sortBy,
    filters.sortDir,
  ].join("|");
}
