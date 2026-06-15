import { useCallback, useMemo, useState } from "react";
import {
  AlertTriangle,
  Clock3,
  Factory,
  Gauge,
  Inbox,
  RefreshCw,
  TrendingUp,
} from "lucide-react";

import { AppointmentsTable } from "../components/AppointmentsTable";
import { DashboardCharts } from "../components/DashboardCharts";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import {
  PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD,
  PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
  PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
} from "../constants/businessRules";
import { buildEficienciaFabrilAppointmentPath } from "../constants/routes";
import { useEficienciaFabrilDashboard } from "../hooks/useEficienciaFabrilDashboard";
import { useEficienciaFabrilFilters } from "../hooks/useEficienciaFabrilFilters";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import {
  BRANCH_ROUTE_LABELS,
  branchRouteFromPathname,
  totvsBranchFromRoute,
} from "../constants/branches";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import { formatPeriodLabel } from "../utils/dates";
import { EFFICIENCY_KPI_WARNING_PCT } from "../constants/businessRules";
import { formatCurrency, formatHoursKpi, formatPercent } from "../utils/format";
import { EFFICIENCY_BAND_FILTER_OPTIONS } from "../constants/efficiencyBands";
import {
  buildEmployeeFilterOptions,
  buildOpFilterOptions,
  buildShiftFilterOptions,
  buildWorkCenterFilterOptions,
} from "../utils/filterOptions";
import { navigateEficienciaFabril } from "../utils/navigation";

type DashboardEficienciaFabrilPageProps = {
  pathname?: string;
};

export function DashboardEficienciaFabrilPage({ pathname }: DashboardEficienciaFabrilPageProps) {
  const branchRoute = branchRouteFromPathname(pathname);
  const totvsBranch = branchRoute ? totvsBranchFromRoute(branchRoute) : null;

  if (!branchRoute || !totvsBranch) {
    return (
      <div className="dashboard-eficiencia-fabril dashboard-page">
        <div className="ef-app-shell">
        <div className="ef-alert ef-alert--error" role="alert">
          <AlertTriangle size={18} aria-hidden />
          <span>
            Filial inválida. Use uma rota como /apps/eficiencia-fabril/sc ou
            /apps/eficiencia-fabril/es.
          </span>
        </div>
        </div>
      </div>
    );
  }

  return (
    <DashboardEficienciaFabrilContent
      key={totvsBranch}
      branchRoute={branchRoute}
      totvsBranch={totvsBranch}
    />
  );
}

type DashboardContentProps = {
  branchRoute: "SC" | "ES";
  totvsBranch: string;
};

function DashboardEficienciaFabrilContent({
  branchRoute,
  totvsBranch,
}: DashboardContentProps) {
  const {
    dateStart,
    dateEnd,
    appliedDateStart,
    appliedDateEnd,
    ops,
    employees,
    workCenters,
    shifts,
    efficiencyBands,
    sortBy,
    sortDir,
    page,
    setDateStart,
    setDateEnd,
    setOps,
    setEmployees,
    setWorkCenters,
    setShifts,
    setEfficiencyBands,
    setPage,
    toggleSortColumn,
    apiParams,
  } = useEficienciaFabrilFilters(totvsBranch);

  const [exportError, setExportError] = useState<string | null>(null);
  const handleExportError = useCallback((message: string) => {
    setExportError(message);
  }, []);

  const handleAppointmentRowClick = useCallback(
    (item: EficienciaFabrilItem) => {
      if (!item.appointment_id) return;
      navigateEficienciaFabril(
        buildEficienciaFabrilAppointmentPath(
          branchRoute,
          item.appointment_id,
          item.filial ?? totvsBranch
        )
      );
    },
    [branchRoute, totvsBranch]
  );

  const { data, allItems, loadedItems, loading, error, reload } =
    useEficienciaFabrilDashboard(apiParams);

  const shiftOptions = useMemo(() => buildShiftFilterOptions(), []);
  const efficiencyBandOptions = useMemo(() => EFFICIENCY_BAND_FILTER_OPTIONS, []);
  const opOptions = useMemo(() => buildOpFilterOptions(loadedItems), [loadedItems]);
  const employeeOptions = useMemo(
    () => buildEmployeeFilterOptions(loadedItems),
    [loadedItems]
  );
  const workCenterOptions = useMemo(
    () => buildWorkCenterFilterOptions(loadedItems),
    [loadedItems]
  );

  const summary = data?.summary;
  const pagination = data?.pagination;
  const charts = data?.charts;
  const hasData = data !== null;
  const refreshing = loading && hasData;
  const isEmpty = hasData && (summary?.table_appointment_count ?? 0) === 0;
  const initialFetchProgress = useTrackedSingleFetchProgress(loading && !hasData);
  const refreshFetchProgress = useTrackedSingleFetchProgress(refreshing);
  const initialLoadingProgress = useLoadingProgress(loading && !hasData, initialFetchProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing, refreshFetchProgress);

  return (
    <div className="dashboard-eficiencia-fabril dashboard-page">
      <div className="ef-app-shell">
      <header className="ef-page-header">
        <div className="ef-page-header__title">
          <div className="ef-header__icon" aria-hidden="true">
            <Factory size={28} strokeWidth={1.75} />
          </div>
          <div>
            <h1>Eficiência Fabril — {branchRoute}</h1>
            <p>
              {BRANCH_ROUTE_LABELS[branchRoute]} ·{" "}
              {formatPeriodLabel(appliedDateStart, appliedDateEnd)}
            </p>
          </div>
        </div>
        <button
          type="button"
          className="ef-btn ef-btn--ghost"
          onClick={() => reload()}
          disabled={loading}
        >
          <RefreshCw size={16} className={refreshing ? "ef-spin" : undefined} aria-hidden />
          {refreshing ? "Atualizando…" : "Atualizar"}
        </button>
      </header>

      <FilterBar
        dateStart={dateStart}
        dateEnd={dateEnd}
        ops={ops}
        employees={employees}
        workCenters={workCenters}
        shifts={shifts}
        efficiencyBands={efficiencyBands}
        opOptions={opOptions}
        employeeOptions={employeeOptions}
        workCenterOptions={workCenterOptions}
        shiftOptions={shiftOptions}
        efficiencyBandOptions={efficiencyBandOptions}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onOpsChange={setOps}
        onEmployeesChange={setEmployees}
        onWorkCentersChange={setWorkCenters}
        onShiftsChange={setShifts}
        onEfficiencyBandsChange={setEfficiencyBands}
        disabled={loading}
      />

      <p className="ef-efficiency-legend ef-efficiency-legend--warning">
        Atenção: apontamentos com eficiência fora da faixa {PRODUCTION_EFFICIENCY_VALID_MIN_PCT}–
        {PRODUCTION_EFFICIENCY_VALID_MAX_PCT}% são desconsiderados no indicador de eficiência (KPIs e
        gráficos) e aparecem na tabela como &quot;Verificar&quot;. Apontamentos na faixa válida com
        eficiência abaixo de {PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD}% aparecem como
        &quot;Eficiência baixa&quot; — abra o detalhe para verificar o motivo.
      </p>

      {error || exportError ? (
        <div className="ef-alert ef-alert--error" role="alert">
          <AlertTriangle size={18} aria-hidden />
          <span>{error ?? exportError}</span>
        </div>
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando eficiência fabril"
          description="Buscando indicadores, gráficos e apontamentos no período."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      {refreshing ? (
        <LoadingActivityCard
          title="Atualizando dashboard"
          description="Recalculando eficiência e apontamentos com os filtros selecionados."
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
        {summary ? (
          <section className="ef-kpi-grid" aria-label="Indicadores">
            <KpiCard
              label="Eficiência"
              value={formatPercent(summary.weighted_efficiency_pct)}
              hint="Média da eficiência (%)"
              tone={
                summary.weighted_efficiency_pct !== null &&
                summary.weighted_efficiency_pct < EFFICIENCY_KPI_WARNING_PCT
                  ? "negative"
                  : "default"
              }
              icon={<Gauge size={22} />}
            />
            <KpiCard
              label="Apontamentos"
              value={summary.table_appointment_count.toLocaleString("pt-BR")}
              hint={`${summary.verify_appointment_count.toLocaleString("pt-BR")} fora da faixa · ${summary.low_efficiency_appointment_count.toLocaleString("pt-BR")} eficiência baixa`}
              icon={<Factory size={22} />}
            />
            <KpiCard
              label="Resultado MOD"
              value={formatCurrency(summary.total_mod_result)}
              tone={(summary.total_mod_result ?? 0) >= 0 ? "positive" : "negative"}
              icon={<TrendingUp size={22} />}
            />
            <KpiCard
              label="Horas ganhas/perdidas"
              value={formatHoursKpi(summary.total_hours_gained_lost, 2)}
              hint="Positivo = economia de tempo"
              icon={<Clock3 size={22} />}
            />
          </section>
        ) : null}

        {isEmpty ? (
          <div className="ef-empty-state" role="status">
            <Inbox size={32} aria-hidden />
            <p>Nenhum apontamento encontrado para os filtros selecionados.</p>
            <p className="ef-empty-state__hint">
              Amplie o período ou ajuste os demais filtros.
            </p>
          </div>
        ) : null}

        {charts && !isEmpty ? <DashboardCharts charts={charts} /> : null}

        {data && !isEmpty ? (
          <AppointmentsTable
            items={data.items}
            exportItems={allItems}
            exportDateStart={appliedDateStart}
            exportDateEnd={appliedDateEnd}
            page={pagination?.page ?? page}
            totalPages={pagination?.total_pages ?? 1}
            total={pagination?.total ?? 0}
            sortBy={sortBy}
            sortDir={sortDir}
            onSortChange={toggleSortColumn}
            onPageChange={setPage}
            onRowClick={handleAppointmentRowClick}
            onExportError={handleExportError}
            disabled={loading}
          />
        ) : null}
      </div>
      </div>
    </div>
  );
}
