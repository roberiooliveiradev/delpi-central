import {
  AlertTriangle,
  Clock3,
  Factory,
  Gauge,
  RefreshCw,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { AppointmentsTable } from "../components/AppointmentsTable";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { useEficienciaFabrilDashboard } from "../hooks/useEficienciaFabrilDashboard";
import { useEficienciaFabrilFilters } from "../hooks/useEficienciaFabrilFilters";
import { formatPeriodLabel } from "../utils/dates";
import { formatCurrency, formatNumber, formatPercent } from "../utils/format";

export function DashboardEficienciaFabrilPage() {
  const {
    branches,
    dateStart,
    dateEnd,
    branch,
    employee,
    workCenter,
    statusOkOnly,
    page,
    setDateStart,
    setDateEnd,
    setBranch,
    setEmployee,
    setWorkCenter,
    setStatusOkOnly,
    setPage,
    resetPage,
    apiParams,
  } = useEficienciaFabrilFilters();

  const { data, loading, error, reload } = useEficienciaFabrilDashboard(apiParams);

  const summary = data?.summary;
  const pagination = data?.pagination;
  const charts = data?.charts;

  const handleApplyFilters = () => {
    if (page !== 1) {
      resetPage();
      return;
    }
    reload();
  };

  const handlePageChange = (nextPage: number) => {
    setPage(nextPage);
  };

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
          <RefreshCw size={16} aria-hidden />
          Atualizar
        </button>
      </header>

      <FilterBar
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        employee={employee}
        workCenter={workCenter}
        statusOkOnly={statusOkOnly}
        branches={branches}
        onDateStartChange={(value) => {
          setDateStart(value);
          resetPage();
        }}
        onDateEndChange={(value) => {
          setDateEnd(value);
          resetPage();
        }}
        onBranchChange={(value) => {
          setBranch(value);
          resetPage();
        }}
        onEmployeeChange={setEmployee}
        onWorkCenterChange={setWorkCenter}
        onStatusOkOnlyChange={(value) => {
          setStatusOkOnly(value);
          resetPage();
        }}
        onApply={handleApplyFilters}
        loading={loading}
      />

      <p className="ef-efficiency-legend">
        Eficiência &gt; 100% indica produção mais rápida que o tempo previsto.
      </p>

      {error ? (
        <div className="ef-alert ef-alert--error" role="alert">
          <AlertTriangle size={18} aria-hidden />
          <span>{error}</span>
        </div>
      ) : null}

      {loading && !data ? (
        <div className="ef-loading-card">Carregando dashboard…</div>
      ) : null}

      {summary ? (
        <section className="ef-kpi-grid" aria-label="Indicadores">
          <KpiCard
            label="Eficiência ponderada"
            value={formatPercent(summary.weighted_efficiency_pct)}
            hint="Σ previsto / Σ real × 100 (registros OK)"
            icon={<Gauge size={20} />}
          />
          <KpiCard
            label="Apontamentos OK"
            value={summary.appointment_count.toLocaleString("pt-BR")}
            hint={`${summary.invalid_record_count.toLocaleString("pt-BR")} com problema no período`}
            icon={<Factory size={20} />}
          />
          <KpiCard
            label="Resultado MOD"
            value={formatCurrency(summary.total_mod_result)}
            tone={
              (summary.total_mod_result ?? 0) >= 0 ? "positive" : "negative"
            }
            icon={<TrendingUp size={20} />}
          />
          <KpiCard
            label="Lucro MOD"
            value={formatCurrency(summary.total_mod_profit)}
            tone="positive"
            icon={<TrendingUp size={20} />}
          />
          <KpiCard
            label="Prejuízo MOD"
            value={formatCurrency(summary.total_mod_loss)}
            tone="negative"
            icon={<TrendingDown size={20} />}
          />
          <KpiCard
            label="Horas ganhas/perdidas"
            value={formatNumber(summary.total_hours_gained_lost, 2)}
            hint="Positivo = economia de tempo"
            icon={<Clock3 size={20} />}
          />
        </section>
      ) : null}

      {charts ? (
        <section className="ef-preview-grid" aria-label="Prévia analítica">
          <article className="ef-preview-card">
            <h2>Eficiência por dia</h2>
            <ul>
              {charts.efficiency_by_day.slice(-5).map((row) => (
                <li key={String(row.date)}>
                  <span>{String(row.date)}</span>
                  <strong>{formatPercent(row.efficiency_pct)}</strong>
                </li>
              ))}
            </ul>
          </article>
          <article className="ef-preview-card">
            <h2>Top operadores</h2>
            <ul>
              {charts.efficiency_by_operator.slice(0, 5).map((row) => (
                <li key={`${row.operator_code}-${row.operator_login}`}>
                  <span>{row.operator_name ?? row.operator_login ?? "—"}</span>
                  <strong>{formatPercent(row.efficiency_pct)}</strong>
                </li>
              ))}
            </ul>
          </article>
        </section>
      ) : null}

      {data ? (
        <AppointmentsTable
          items={data.items}
          page={pagination?.page ?? page}
          totalPages={pagination?.total_pages ?? 1}
          total={pagination?.total ?? 0}
          onPageChange={handlePageChange}
        />
      ) : null}
    </div>
  );
}
