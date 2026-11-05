/**
 * Invalidação direcionada das consultas do fechamento.
 * Só deve ser chamada depois que a escrita devolveu a entidade persistida.
 */
import {
  getActiveReportCacheScope,
  getReportQueryClient,
} from "./reportQueryCache";
import {
  p3QueryKey,
  reportMatrixQueryKey,
  settlementsSummaryQueryKey,
  stockInventoryQueryKey,
  stockReconciliationQueryKey,
} from "./reportQueryKeys";

function periodRange(period: string): { startDate: string; endDate: string } {
  const [year, month] = period.split("-").map(Number);
  const lastDay = new Date(year, month, 0).getDate();
  return {
    startDate: `${period}-01`,
    endDate: `${period}-${String(lastDay).padStart(2, "0")}`,
  };
}

export function invalidateP3(period: string): void {
  const scope = getActiveReportCacheScope();
  if (!scope || !period) return;
  void getReportQueryClient().invalidateQueries({
    queryKey: p3QueryKey(scope, period),
  });
}

export function invalidateReportMatrix(period: string): void {
  const scope = getActiveReportCacheScope();
  if (!scope || !period) return;
  void getReportQueryClient().invalidateQueries({
    queryKey: [...reportMatrixQueryKey(scope, period).slice(0, -1)],
  });
}

export function invalidateReportMatrixIfPersisted(
  period: string,
  entity: unknown,
): void {
  if (entity == null) return;
  invalidateReportMatrix(period);
}

export function invalidateVisibleReports(period: string): void {
  const scope = getActiveReportCacheScope();
  if (!scope || !period) return;
  const client = getReportQueryClient();
  const range = periodRange(period);
  void client.invalidateQueries({ queryKey: p3QueryKey(scope, period) });
  void client.invalidateQueries({
    queryKey: [...reportMatrixQueryKey(scope, period).slice(0, -1)],
  });
  void client.invalidateQueries({
    queryKey: settlementsSummaryQueryKey(scope, range),
  });
  void client.invalidateQueries({
    queryKey: [...stockInventoryQueryKey(scope, { period }).slice(0, 6)],
  });
  void client.invalidateQueries({
    queryKey: [...stockReconciliationQueryKey(scope, { period }).slice(0, 6)],
  });
}
