/**
 * Chaves de cache das consultas do fechamento mensal.
 * O segmento de escopo discrimina identidade e autorização observável.
 * Não inclui Bearer, JWT nem segredo.
 */

export type ReportCacheScope = {
  subject: string;
  authzFingerprint: string;
  generation: number;
};

export const REPORT_GC_TIME_MS = 1_800_000;
export const REPORT_STALE_WORKFLOW_MS = 60_000;
export const REPORT_STALE_OPERATIONAL_MS = 300_000;

/** Ausência de `branch_scope` na BFF equivale a BOTH. */
export const HUB_MATRIX_BRANCH_SCOPE = "BOTH";
export const HUB_STOCK_BRANCH = "all";
export const HUB_REPORT_SCOPE = "all_products";
export const HUB_STOCK_PAGE = 1;
export const HUB_STOCK_PAGE_SIZE = 25;

export type ReportSourceName =
  | "p3"
  | "report-matrix"
  | "settlements-summary"
  | "stock-inventory"
  | "stock-reconciliation";

function scopeParts(scope: ReportCacheScope): readonly [string, string, number] {
  return [scope.subject, scope.authzFingerprint, scope.generation];
}

export function p3QueryKey(scope: ReportCacheScope, period: string) {
  return ["cf", ...scopeParts(scope), "p3", period] as const;
}

export function reportMatrixQueryKey(
  scope: ReportCacheScope,
  period: string,
  branchScope: string = HUB_MATRIX_BRANCH_SCOPE,
) {
  return ["cf", ...scopeParts(scope), "report-matrix", period, branchScope] as const;
}

export function settlementsSummaryQueryKey(
  scope: ReportCacheScope,
  input: {
    startDate: string;
    endDate: string;
    natureCode?: string;
    movementType?: string;
  },
) {
  return [
    "cf",
    ...scopeParts(scope),
    "settlements-summary",
    input.startDate,
    input.endDate,
    input.natureCode ?? "",
    input.movementType ?? "",
  ] as const;
}

export function stockInventoryQueryKey(
  scope: ReportCacheScope,
  input: {
    period: string;
    branch?: string;
    reportScope?: string;
    warehouse?: string;
    page?: number;
    pageSize?: number;
  },
) {
  return [
    "cf",
    ...scopeParts(scope),
    "stock-inventory",
    input.period,
    input.branch ?? HUB_STOCK_BRANCH,
    input.reportScope ?? HUB_REPORT_SCOPE,
    input.warehouse ?? "",
    input.page ?? HUB_STOCK_PAGE,
    input.pageSize ?? HUB_STOCK_PAGE_SIZE,
  ] as const;
}

export function stockReconciliationQueryKey(
  scope: ReportCacheScope,
  input: {
    period: string;
    branch?: string;
    reportScope?: string;
  },
) {
  return [
    "cf",
    ...scopeParts(scope),
    "stock-reconciliation",
    input.period,
    input.branch ?? HUB_STOCK_BRANCH,
    input.reportScope ?? HUB_REPORT_SCOPE,
  ] as const;
}
