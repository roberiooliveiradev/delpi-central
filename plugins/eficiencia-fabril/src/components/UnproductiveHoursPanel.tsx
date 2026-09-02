import { AlertTriangle, Inbox } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useUnproductiveHoursDashboard } from "../hooks/useUnproductiveHoursDashboard";
import { useUnproductiveHoursItems } from "../hooks/useUnproductiveHoursItems";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import type {
  UnproductiveHoursFilterFormState,
  UnproductiveHoursQueryFilters,
  UnproductiveHoursSort,
} from "../types/unproductiveHours";
import {
  createDefaultUnproductiveHoursFilterForm,
  resolveItemsPagination,
  resolveSummaryNumber,
} from "../types/unproductiveHours";
import { LoadingActivityCard } from "./LoadingActivityCard";
import { UnproductiveHoursCharts } from "./UnproductiveHoursCharts";
import { UnproductiveHoursFilterBar } from "./UnproductiveHoursFilterBar";
import { UnproductiveHoursSummaryCards } from "./UnproductiveHoursSummaryCards";
import { UnproductiveHoursTable } from "./UnproductiveHoursTable";

type UnproductiveHoursPanelProps = {
  branch: string;
  dateStart: string;
  dateEnd: string;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  enabled: boolean;
  onReloadReady?: (reload: () => void) => void;
};

function toQueryFilters(
  branch: string,
  dateStart: string,
  dateEnd: string,
  form: UnproductiveHoursFilterFormState,
): UnproductiveHoursQueryFilters {
  return {
    branch,
    start_date: dateStart,
    end_date: dateEnd,
    stop_reason: form.stopReason.trim() || undefined,
    resource: form.resource.trim() || undefined,
    cost_center: form.costCenter.trim() || undefined,
    operator_code: form.operatorCode.trim() || undefined,
  };
}

export function UnproductiveHoursPanel({
  branch,
  dateStart,
  dateEnd,
  onDateStartChange,
  onDateEndChange,
  enabled,
  onReloadReady,
}: UnproductiveHoursPanelProps) {
  const [form, setForm] = useState<UnproductiveHoursFilterFormState>(
    createDefaultUnproductiveHoursFilterForm,
  );
  const debouncedForm = useDebouncedValue(form, 350);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<UnproductiveHoursSort>("date_desc");
  const [exportError, setExportError] = useState<string | null>(null);

  const filters = useMemo(
    () => toQueryFilters(branch, dateStart, dateEnd, debouncedForm),
    [branch, dateStart, dateEnd, debouncedForm],
  );

  const filtersKey = `${filters.branch}|${filters.start_date}|${filters.end_date}|${filters.stop_reason ?? ""}|${filters.resource ?? ""}|${filters.cost_center ?? ""}|${filters.operator_code ?? ""}`;

  useEffect(() => {
    setPage(1);
  }, [filtersKey]);

  const dashboard = useUnproductiveHoursDashboard(filters, enabled);
  const itemsQuery = useUnproductiveHoursItems(filters, page, sort, enabled);

  useEffect(() => {
    if (!onReloadReady) return;
    onReloadReady(() => {
      dashboard.reload();
      itemsQuery.reload();
    });
  }, [dashboard.reload, itemsQuery.reload, onReloadReady]);

  const loading = dashboard.loading || itemsQuery.loading;
  const error = dashboard.error ?? itemsQuery.error ?? exportError;
  const summary = dashboard.data?.summary.summary;
  const hasDashboard = dashboard.data !== null;
  const hasItems = itemsQuery.data !== null;
  const hasAnyData = hasDashboard || hasItems;
  const refreshing = loading && hasAnyData;
  const paging = resolveItemsPagination(itemsQuery.data);
  const totalAppointments = resolveSummaryNumber(summary, "total_appointments", "totalApontamentos");
  const isEmpty = hasDashboard && totalAppointments === 0;

  const initialFetchProgress = useTrackedSingleFetchProgress(loading && !hasAnyData);
  const refreshFetchProgress = useTrackedSingleFetchProgress(refreshing);
  const initialLoadingProgress = useLoadingProgress(loading && !hasAnyData, initialFetchProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing, refreshFetchProgress);

  return (
    <div className="ef-unproductive-panel">
      <UnproductiveHoursFilterBar
        dateStart={dateStart}
        dateEnd={dateEnd}
        filters={form}
        onDateStartChange={onDateStartChange}
        onDateEndChange={onDateEndChange}
        onFiltersChange={setForm}
        disabled={loading && !hasAnyData}
      />

      {error ? (
        <div className="ef-alert ef-alert--error" role="alert">
          <AlertTriangle size={18} aria-hidden />
          <span>{error}</span>
        </div>
      ) : null}

      {loading && !hasAnyData ? (
        <LoadingActivityCard
          title="Carregando horas improdutivas"
          description="Buscando paradas apontadas pelos operadores no período."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      {refreshing ? (
        <LoadingActivityCard
          title="Atualizando horas improdutivas"
          description="Recalculando indicadores, rankings e apontamentos."
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      <div
        className={
          refreshing ? "ef-dashboard-body ef-dashboard-body--refreshing" : "ef-dashboard-body"
        }
      >
        {summary ? <UnproductiveHoursSummaryCards summary={summary} /> : null}

        {isEmpty ? (
          <div className="ef-empty-state" role="status">
            <Inbox size={32} aria-hidden />
            <p>Nenhuma hora improdutiva encontrada para os filtros selecionados.</p>
            <p className="ef-empty-state__hint">Amplie o período ou limpe os filtros de motivo/recurso.</p>
          </div>
        ) : null}

        {!isEmpty && dashboard.data ? (
          <UnproductiveHoursCharts
            byStopReason={dashboard.data.byStopReason.items ?? []}
            byOperator={dashboard.data.byOperator.items ?? []}
            byResource={dashboard.data.byResource.items ?? []}
          />
        ) : null}

        {!isEmpty && itemsQuery.data ? (
          <UnproductiveHoursTable
            items={itemsQuery.data.items ?? []}
            filters={filters}
            page={paging.page}
            totalPages={paging.totalPages}
            total={paging.total}
            sort={sort}
            onSortChange={(next) => {
              setSort(next);
              setPage(1);
            }}
            onPageChange={setPage}
            onExportError={setExportError}
            disabled={loading}
          />
        ) : null}
      </div>
    </div>
  );
}
