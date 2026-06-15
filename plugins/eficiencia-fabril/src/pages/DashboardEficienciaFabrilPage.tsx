import { useCallback, useState } from "react";
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
import {
  PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
  PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
} from "../constants/businessRules";
import { buildEficienciaFabrilAppointmentPath } from "../constants/routes";
import { useEficienciaFabrilDashboard } from "../hooks/useEficienciaFabrilDashboard";
import { useEficienciaFabrilFilters } from "../hooks/useEficienciaFabrilFilters";
import {
  BRANCH_ROUTE_LABELS,
  branchRouteFromPathname,
  totvsBranchFromRoute,
} from "../constants/branches";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import { formatPeriodLabel } from "../utils/dates";
import { EFFICIENCY_KPI_WARNING_PCT } from "../constants/businessRules";
import { formatCurrency, formatHoursKpi, formatPercent } from "../utils/format";
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
    op,
    employee,
    workCenter,
    shift,
    hasPendingChanges,
    page,
    setDateStart,
    setDateEnd,
    setOp,
    setEmployee,
    setWorkCenter,
    setShift,
    setPage,
    applyFilters,
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

  const { data, allItems, loading, error, reload } = useEficienciaFabrilDashboard(apiParams);

  const summary = data?.summary;
  const pagination = data?.pagination;
  const charts = data?.charts;
  const refreshing = loading && Boolean(data);
  const isEmpty = Boolean(data) && (summary?.table_appointment_count ?? 0) === 0;

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
              {BRANCH_ROUTE_LABELS[branchRoute]} · {formatPeriodLabel(dateStart, dateEnd)}
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
        op={op}
        employee={employee}
        workCenter={workCenter}
        shift={shift}
        hasPendingChanges={hasPendingChanges}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onOpChange={setOp}
        onEmployeeChange={setEmployee}
        onWorkCenterChange={setWorkCenter}
        onShiftChange={setShift}
        onApply={() => {
          setExportError(null);
          applyFilters();
        }}
        loading={loading}
      />

      <p className="ef-efficiency-legend ef-efficiency-legend--warning">
        Atenção: apontamentos com eficiência fora da faixa {PRODUCTION_EFFICIENCY_VALID_MIN_PCT}–
        {PRODUCTION_EFFICIENCY_VALID_MAX_PCT}% são desconsiderados no indicador de eficiência (KPIs e
        gráficos) e aparecem na tabela como &quot;Verificar&quot;.
      </p>

      {error || exportError ? (
        <div className="ef-alert ef-alert--error" role="alert">
          <AlertTriangle size={18} aria-hidden />
          <span>{error ?? exportError}</span>
        </div>
      ) : null}

      {loading && !data ? (
        <div className="ef-loading-card">Carregando dashboard…</div>
      ) : null}

      {refreshing ? (
        <div className="ef-loading-card ef-loading-card--refresh" role="status" aria-live="polite">
          <span className="ef-loading-card__spinner" aria-hidden />
          <div>
            <strong>Atualizando dashboard</strong>
            <p>Recalculando eficiência e apontamentos com os filtros selecionados.</p>
          </div>
        </div>
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
              hint={`${summary.verify_appointment_count.toLocaleString("pt-BR")} a avaliar (Verificar)`}
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
            exportDateStart={apiParams.date_start}
            exportDateEnd={apiParams.date_end}
            page={pagination?.page ?? page}
            totalPages={pagination?.total_pages ?? 1}
            total={pagination?.total ?? 0}
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
