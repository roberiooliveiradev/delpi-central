import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { ApiError } from "../../api/httpClient";
import { getFinancialSettlementsSummary } from "../../api/financialSettlementsApi";
import { getStockInventory } from "../../api/stockInventoryApi";
import {
  getStockReconciliation,
  type StockReconciliationPayload,
} from "../../api/stockReconciliationApi";
import type { StockInventoryBranch } from "../../api/stockInventoryApi";
import { getP3State, type P3Status } from "../../api/p3Api";
import { listReportMatrix, type ReportMatrix } from "../../api/reportsApi";
import {
  guardReportQuery,
  isReportSessionSealed,
  reconcileReportCacheScope,
  type GuardedResult,
} from "../../app/reportQueryCache";
import {
  useReportCacheScope,
  useReportSessionSealed,
} from "../../app/ControllershipQueryProvider";
import { invalidateVisibleReports } from "../../app/reportQueryInvalidation";
import {
  HUB_MATRIX_BRANCH_SCOPE,
  HUB_STOCK_PAGE,
  HUB_STOCK_PAGE_SIZE,
  REPORT_GC_TIME_MS,
  REPORT_STALE_OPERATIONAL_MS,
  REPORT_STALE_WORKFLOW_MS,
  p3QueryKey,
  reportMatrixQueryKey,
  settlementsSummaryQueryKey,
  stockInventoryQueryKey,
  stockReconciliationQueryKey,
  type ReportCacheScope,
} from "../../app/reportQueryKeys";

/** Filiais da visão analítica — consultas independentes à BFF. */
export const ANALYTICAL_RECON_BRANCHES = ["01", "02", "all"] as const;
export type AnalyticalReconBranch =
  (typeof ANALYTICAL_RECON_BRANCHES)[number];

export type ReportPanelError = {
  status: number;
  code: string | null;
  message: string;
};

const ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para esta consulta.",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  competence_not_opened: "Competência não aberta.",
  competence_not_found: "Competência não encontrada.",
  not_found: "Competência não encontrada.",
};

const NOT_OPENED_CODES = new Set([
  "competence_not_opened",
  "competence_not_found",
]);

export type ReportSource<T> =
  | { kind: "ready"; data: T; at: Date }
  | { kind: "not_opened" }
  | { kind: "error"; error: ReportPanelError };

export function mapReportError(error: unknown): ReportPanelError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code ?? null,
      message: ERROR_MESSAGES[error.code ?? ""] ?? error.message,
    };
  }
  return {
    status: 0,
    code: null,
    message: "Falha de comunicação com a API.",
  };
}

function isNotOpened(error: ApiError): boolean {
  return (
    (error.code !== null && NOT_OPENED_CODES.has(error.code)) ||
    error.status === 404
  );
}

const TEST_SCOPE: ReportCacheScope = {
  subject: "vitest",
  authzFingerprint: "0:",
  generation: 0,
};

function resolveScope(
  contextScope: ReportCacheScope | { state: "unauthenticated" } | null,
  sealed: boolean,
): ReportCacheScope | null {
  if (sealed) return null;
  if (contextScope && "subject" in contextScope) return contextScope;
  if (contextScope) return null;
  if (import.meta.env.MODE === "test") {
    return reconcileReportCacheScope(
      TEST_SCOPE.subject,
      TEST_SCOPE.authzFingerprint,
    );
  }
  return null;
}

function viewOf<T>(
  result: GuardedResult<T> | undefined,
  error: unknown,
  isError: boolean,
  isPending: boolean,
): { source: ReportSource<T> | null; refreshError: ReportPanelError | null; fetchedAt: number | null } {
  if (result?.kind === "unauthorized") {
    return {
      source: {
        kind: "error",
        error: {
          status: 401,
          code: "unauthorized",
          message: ERROR_MESSAGES.unauthorized,
        },
      },
      refreshError: null,
      fetchedAt: null,
    };
  }
  if (result?.kind === "forbidden") {
    return {
      source: {
        kind: "error",
        error: {
          status: 403,
          code: "forbidden",
          message: ERROR_MESSAGES.forbidden,
        },
      },
      refreshError: null,
      fetchedAt: null,
    };
  }
  if (result?.kind === "not_opened") {
    return { source: { kind: "not_opened" }, refreshError: null, fetchedAt: null };
  }
  if (result?.kind === "ready") {
    return {
      source: { kind: "ready", data: result.data, at: new Date(result.fetchedAt) },
      refreshError: isError ? mapReportError(error) : null,
      fetchedAt: result.fetchedAt,
    };
  }
  if (isError) {
    return {
      source: { kind: "error", error: mapReportError(error) },
      refreshError: null,
      fetchedAt: null,
    };
  }
  if (isPending) {
    return { source: null, refreshError: null, fetchedAt: null };
  }
  return { source: null, refreshError: null, fetchedAt: null };
}

function periodRange(period: string): { startDate: string; endDate: string } {
  const [year, month] = period.split("-").map(Number);
  const lastDay = new Date(year, month, 0).getDate();
  return {
    startDate: `${period}-01`,
    endDate: `${period}-${String(lastDay).padStart(2, "0")}`,
  };
}

export function useMonthlyReportSources(period: string) {
  const contextScope = useReportCacheScope();
  const sealed = useReportSessionSealed();
  const scope = resolveScope(contextScope, sealed || isReportSessionSealed());
  const enabled = Boolean(period) && scope !== null;
  const range = useMemo(() => (period ? periodRange(period) : null), [period]);

  const p3Key = scope ? p3QueryKey(scope, period) : ["cf", "p3", "disabled", period];
  const matrixKey = scope
    ? reportMatrixQueryKey(scope, period, HUB_MATRIX_BRANCH_SCOPE)
    : ["cf", "report-matrix", "disabled", period];
  const settlementsKey = scope && range
    ? settlementsSummaryQueryKey(scope, range)
    : ["cf", "settlements-summary", "disabled", period];
  const stockKey = scope
    ? stockInventoryQueryKey(scope, {
        period,
        page: HUB_STOCK_PAGE,
        pageSize: HUB_STOCK_PAGE_SIZE,
      })
    : ["cf", "stock-inventory", "disabled", period];
  const reconKey01 = scope
    ? stockReconciliationQueryKey(scope, { period, branch: "01" })
    : ["cf", "stock-reconciliation", "disabled", period, "01"];
  const reconKey02 = scope
    ? stockReconciliationQueryKey(scope, { period, branch: "02" })
    : ["cf", "stock-reconciliation", "disabled", period, "02"];
  const reconKeyAll = scope
    ? stockReconciliationQueryKey(scope, { period, branch: "all" })
    : ["cf", "stock-reconciliation", "disabled", period, "all"];

  const p3Query = useQuery({
    queryKey: p3Key,
    enabled,
    staleTime: REPORT_STALE_WORKFLOW_MS,
    gcTime: REPORT_GC_TIME_MS,
    queryFn: async ({ signal }): Promise<GuardedResult<P3Status>> => {
      const result = await guardReportQuery(
        scope!,
        p3Key,
        signal,
        (next) => getP3State(period, next),
        { emptyIsNotOpened: true, notOpened: isNotOpened },
      );
      if (result.kind === "ready" && result.data == null) return { kind: "not_opened" };
      return result as GuardedResult<P3Status>;
    },
  });
  const matrixQuery = useQuery({
    queryKey: matrixKey,
    enabled,
    staleTime: REPORT_STALE_WORKFLOW_MS,
    gcTime: REPORT_GC_TIME_MS,
    queryFn: async ({ signal }): Promise<GuardedResult<ReportMatrix>> => {
      const result = await guardReportQuery(
        scope!,
        matrixKey,
        signal,
        (next) => listReportMatrix(period, next),
        { emptyIsNotOpened: true, notOpened: isNotOpened },
      );
      if (result.kind === "ready" && result.data == null) return { kind: "not_opened" };
      return result as GuardedResult<ReportMatrix>;
    },
  });
  const settlementsQuery = useQuery({
    queryKey: settlementsKey,
    enabled: enabled && range !== null,
    staleTime: REPORT_STALE_OPERATIONAL_MS,
    gcTime: REPORT_GC_TIME_MS,
    queryFn: ({ signal }) =>
      guardReportQuery(scope!, settlementsKey, signal, (next) =>
        getFinancialSettlementsSummary(
          { startDate: range!.startDate, endDate: range!.endDate },
          { signal: next },
        ),
      ),
  });
  const stockQuery = useQuery({
    queryKey: stockKey,
    enabled,
    staleTime: REPORT_STALE_OPERATIONAL_MS,
    gcTime: REPORT_GC_TIME_MS,
    queryFn: ({ signal }) =>
      guardReportQuery(scope!, stockKey, signal, (next) =>
        getStockInventory(
          { period, page: HUB_STOCK_PAGE, pageSize: HUB_STOCK_PAGE_SIZE },
          { signal: next },
        ),
      ),
  });
  function reconQueryOptions(
    branch: StockInventoryBranch,
    queryKey: readonly unknown[],
  ) {
    return {
      queryKey,
      enabled,
      staleTime: REPORT_STALE_OPERATIONAL_MS,
      gcTime: REPORT_GC_TIME_MS,
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        guardReportQuery(scope!, queryKey, signal, (next) =>
          getStockReconciliation(
            { period, branch },
            { signal: next },
          ),
        ),
    };
  }

  const reconQuery01 = useQuery(
    reconQueryOptions("01", reconKey01),
  );
  const reconQuery02 = useQuery(
    reconQueryOptions("02", reconKey02),
  );
  const reconQueryAll = useQuery(
    reconQueryOptions("all", reconKeyAll),
  );

  const p3 = viewOf(p3Query.data, p3Query.error, p3Query.isError, p3Query.isPending);
  const matrix = viewOf(
    matrixQuery.data,
    matrixQuery.error,
    matrixQuery.isError,
    matrixQuery.isPending,
  );
  const settlements = viewOf(
    settlementsQuery.data,
    settlementsQuery.error,
    settlementsQuery.isError,
    settlementsQuery.isPending,
  );
  const stock = viewOf(
    stockQuery.data,
    stockQuery.error,
    stockQuery.isError,
    stockQuery.isPending,
  );
  const recon01 = viewOf(
    reconQuery01.data,
    reconQuery01.error,
    reconQuery01.isError,
    reconQuery01.isPending,
  );
  const recon02 = viewOf(
    reconQuery02.data,
    reconQuery02.error,
    reconQuery02.isError,
    reconQuery02.isPending,
  );
  const reconAll = viewOf(
    reconQueryAll.data,
    reconQueryAll.error,
    reconQueryAll.isError,
    reconQueryAll.isPending,
  );

  const sources = [p3, matrix, settlements, stock, recon01, recon02, reconAll];
  const fetchedTimes = sources
    .map((source) => source.fetchedAt)
    .filter((value): value is number => value !== null);

  const reconByBranch: Record<
    AnalyticalReconBranch,
    ReportSource<StockReconciliationPayload> | null
  > = {
    "01": recon01.source,
    "02": recon02.source,
    all: reconAll.source,
  };

  return {
    sealed: sealed || isReportSessionSealed(),
    scopeReady: scope !== null,
    p3: p3.source,
    matrix: matrix.source,
    settlements: settlements.source,
    stock: stock.source,
    /** Alias legado = consolidado (`branch=all`). Preferir `reconByBranch`. */
    recon: reconAll.source,
    reconByBranch,
    p3Fetching: p3Query.isFetching,
    matrixFetching: matrixQuery.isFetching,
    settlementsFetching: settlementsQuery.isFetching,
    stockFetching: stockQuery.isFetching,
    reconFetching:
      reconQuery01.isFetching ||
      reconQuery02.isFetching ||
      reconQueryAll.isFetching,
    refreshError:
      p3.refreshError ??
      matrix.refreshError ??
      settlements.refreshError ??
      stock.refreshError ??
      recon01.refreshError ??
      recon02.refreshError ??
      reconAll.refreshError,
    latestFetchedAt: fetchedTimes.length > 0 ? Math.max(...fetchedTimes) : null,
    refetchAll: () => invalidateVisibleReports(period),
  };
}
