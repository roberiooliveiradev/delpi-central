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
import { useEficienciaFabrilDashboard } from "../hooks/useEficienciaFabrilDashboard";
import { useEficienciaFabrilFilters } from "../hooks/useEficienciaFabrilFilters";
import { formatPeriodLabel } from "../utils/dates";
import { EFFICIENCY_KPI_WARNING_PCT } from "../constants/businessRules";
import { formatCurrency, formatHoursKpi, formatPercent } from "../utils/format";

export function DashboardEficienciaFabrilPage() {
  const {
    branches,
    dateStart,
    dateEnd,
    branch,
    op,
    employee,
    workCenter,
    hasPendingChanges,
    page,
    setDateStart,
    setDateEnd,
    setBranch,
    setOp,
    setEmployee,
    setWorkCenter,
    setPage,
    applyFilters,
    apiParams,
  } = useEficienciaFabrilFilters();

  const [exportError, setExportError] = useState<string | null>(null);
  const handleExportError = useCallback((message: string) => {
    setExportError(message);
  }, []);

  const { data, allItems, loading, error, reload } = useEficienciaFabrilDashboard(apiParams);

  const summary = data?.summary;
  const pagination = data?.pagination;
  const charts = data?.charts;
  const refreshing = loading && Boolean(data);
  const isEmpty = Boolean(data) && (summary?.table_appointment_count ?? 0) === 0;

  return (
    <div className="dashboard-eficiencia-fabril dashboard-page">
      <header className="ef-page-header">
        <div className="ef-page-header__title">
          <Factory size={28} aria-hidden />
          <div>
            <h1>Eficiência Fabril</h1>
            <p>{formatPeriodLabel(dateStart, dateEnd)}</p>
          </div>
        </div>
        <button
          type="button"
          className="ef-btn ef-btn--ghost"
          onClick={() => reload()}
          disabled={loading}
        >
          <RefreshCw size={16} className={refreshing ? "ef-spin" : undefined} aria-hidden />
          Atualizar
        </button>
      </header>

      <FilterBar
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        op={op}
        employee={employee}
        workCenter={workCenter}
        branches={branches}
        hasPendingChanges={hasPendingChanges}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onOpChange={setOp}
        onEmployeeChange={setEmployee}
        onWorkCenterChange={setWorkCenter}
        onApply={() => {
          setExportError(null);
          applyFilters();
        }}
        loading={loading}
      />

      <p className="ef-efficiency-legend ef-efficiency-legend--warning">
        Atenção: apontamentos com eficiência acima de 250% são desconsiderados no indicador de
        eficiência (KPIs e gráficos) e aparecem na tabela como &quot;Verificar&quot;.
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
              icon={<Gauge size={20} />}
            />
            <KpiCard
              label="Apontamentos"
              value={summary.table_appointment_count.toLocaleString("pt-BR")}
              hint={`${summary.verify_appointment_count.toLocaleString("pt-BR")} a avaliar (Verificar)`}
              icon={<Factory size={20} />}
            />
            <KpiCard
              label="Resultado MOD"
              value={formatCurrency(summary.total_mod_result)}
              tone={(summary.total_mod_result ?? 0) >= 0 ? "positive" : "negative"}
              icon={<TrendingUp size={20} />}
            />
            <KpiCard
              label="Horas ganhas/perdidas"
              value={formatHoursKpi(summary.total_hours_gained_lost, 2)}
              hint="Positivo = economia de tempo"
              icon={<Clock3 size={20} />}
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
            onExportError={handleExportError}
            disabled={loading}
          />
        ) : null}
      </div>
    </div>
  );
}
