import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Banknote,
  Building2,
  Percent,
  Target,
  UserPlus,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { RolEvolutionChart } from "../components/RolEvolutionChart";
import { TotvsSourceBanner } from "../components/TotvsSourceBanner";
import { CHART_COLORS } from "../constants/chartColors";
import { useCommercialDashboard } from "../hooks/useCommercialDashboard";
import { useCommercialFilters } from "../hooks/useCommercialFilters";
import { useCommercialRolSeries } from "../hooks/useCommercialRolSeries";
import type { ChartGranularity } from "../types/chart";
import { downloadRolSeriesCsv } from "../utils/chartSeriesExport";
import { formatPeriodLabel } from "../utils/dates";
import { suggestGranularity } from "../utils/periodBuckets";
import {
  formatInteger,
  formatCurrency,
  formatDecimal,
  formatPercent,
} from "../utils/format";

const CHART_HEIGHT = 280;

type DashboardCommercialPageProps = {
  pathname?: string;
};

export function DashboardCommercialPage(_props: DashboardCommercialPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useCommercialFilters();

  const [granularity, setGranularity] = useState<ChartGranularity>("month");

  const {
    headOfficeRol,
    branchRol,
    closingRate,
    newClientsAverage,
    newClientsRol,
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  } = useCommercialDashboard(apiParams);

  const periodParams = useMemo(
    () => ({
      start_date: apiParams.start_date,
      end_date: apiParams.end_date,
    }),
    [apiParams.end_date, apiParams.start_date]
  );

  const rolSeries = useCommercialRolSeries({
    filters: periodParams,
    granularity,
  });

  useEffect(() => {
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const isBusy = loading || refreshing;
  const hasData = headOfficeRol !== null || branchRol !== null;
  const isChartBusy = rolSeries.loading;

  const conversionChartData = useMemo(
    () =>
      closingRate
        ? [
            { name: "Propostas", value: closingRate.qtd_proposals },
            { name: "Ganhas", value: closingRate.qtd_won },
          ]
        : [],
    [closingRate]
  );

  const hasChartValues = rolSeries.points.some(
    (point) => point.rolMatrix > 0 || point.rolBranch > 0
  );

  const printDisabled = loading && !hasData;

  const handleChartDrillDown = useCallback(
    (nextStart: string, nextEnd: string) => {
      setDateStart(nextStart);
      setDateEnd(nextEnd);
    },
    [setDateStart, setDateEnd]
  );

  const handleExportChartCsv = useCallback(() => {
    downloadRolSeriesCsv("rol-evolucao.csv", rolSeries.points);
  }, [rolSeries.points]);

  const chartHint =
    "Clique em um ponto para filtrar o período ao intervalo. Matriz (01) e filial (02).";

  return (
    <div className="dashboard-commercial dashboard-page dc-print-root">
      <FilterBar
        filterState={filterState}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        printDisabled={printDisabled}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onRefresh={reload}
        refreshing={refreshing}
      />

      <TotvsSourceBanner />

      {error ? (
        <div className="dc-state dc-state--error" role="alert">
          <p>{error}</p>
          <button className="dc-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {Object.keys(sectionErrors).length > 0 ? (
        <div className="dc-state dc-state--warning" role="status">
          <p>
            Alguns indicadores não carregaram. Os demais permanecem disponíveis.
          </p>
        </div>
      ) : null}

      {loading && !hasData ? (
        <div className="dc-state dc-state--loading" aria-live="polite">
          Carregando indicadores…
        </div>
      ) : null}

      <section className="dc-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="ROL — Matriz (01)"
          value={formatCurrency(headOfficeRol?.rol)}
          subtitle={periodLabel}
          icon={<Banknote size={22} />}
          loading={isBusy && !headOfficeRol}
        />
        <KpiCard
          title="ROL — Filial (02)"
          value={formatCurrency(branchRol?.rol)}
          subtitle={`Filial 02 · ${periodLabel}`}
          icon={<Building2 size={22} />}
          loading={isBusy && !branchRol}
        />
        <KpiCard
          title="Taxa de conversão"
          value={formatPercent(closingRate?.sales_conversion_rate_pct)}
          subtitle={`${formatInteger(closingRate?.qtd_won)} ganhas / ${formatInteger(closingRate?.qtd_proposals)} propostas · ${periodLabel}`}
          icon={<Percent size={22} />}
          loading={isBusy && !closingRate}
        />
        <KpiCard
          title="Média mensal — clientes novos"
          value={formatDecimal(newClientsAverage?.monthly_average, 1)}
          subtitle={`Total ${formatInteger(newClientsAverage?.total_new_clients)} em ${formatInteger(newClientsAverage?.qtd_months)} meses · ${periodLabel}`}
          icon={<UserPlus size={22} />}
          loading={isBusy && !newClientsAverage}
        />
        <KpiCard
          title="% ROL — clientes novos"
          value={formatPercent(newClientsRol?.new_clients_rol_pct)}
          subtitle={branch ? `Filial ${branch} · ${periodLabel}` : periodLabel}
          icon={<Users size={22} />}
          loading={isBusy && !newClientsRol}
        />
      </section>

      <section className="dc-chart-section dc-no-print" aria-busy={isChartBusy}>
        <ChartCard title="Evolução do ROL (R$)" hint={chartHint}>
          <ChartToolbar
            idPrefix="rol"
            granularity={granularity}
            onGranularityChange={setGranularity}
            onExportCsv={handleExportChartCsv}
            exportDisabled={rolSeries.points.length === 0}
          />

          {rolSeries.error ? (
            <div className="dc-state dc-state--error" role="alert">
              <p>{rolSeries.error}</p>
            </div>
          ) : null}

          {!rolSeries.error &&
          (rolSeries.points.length > 0 || rolSeries.loading) ? (
            <RolEvolutionChart
              data={rolSeries.points}
              loading={rolSeries.loading}
              onDrillDown={handleChartDrillDown}
            />
          ) : null}

          {!rolSeries.error &&
          rolSeries.points.length === 0 &&
          !rolSeries.loading ? (
            <div className="dc-state-box">Sem dados para o gráfico no período.</div>
          ) : null}

          {rolSeries.truncated ? (
            <p className="dc-chart-card__hint dc-chart-card__hint--below">
              Período limitado aos primeiros 60 intervalos para desempenho.
            </p>
          ) : null}

          {!rolSeries.error &&
          rolSeries.points.length > 0 &&
          !hasChartValues &&
          !rolSeries.loading ? (
            <p className="dc-chart-card__hint dc-chart-card__hint--below">
              Todos os intervalos retornaram ROL zero no período filtrado.
            </p>
          ) : null}
        </ChartCard>
      </section>

      <section className="dc-charts-grid">
        <ChartCard
          title="Funil de conversão"
          hint="Propostas versus vendas ganhas no período."
        >
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={conversionChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" name="Quantidade" fill={CHART_COLORS[0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>

      <section className="dc-summary-grid dc-no-print">
        <article className="dc-card">
          <div className="dc-summary-card__header">
            <Target size={22} aria-hidden />
            <h2 className="dc-summary-card__title">Como ler os indicadores</h2>
          </div>
          <p className="dc-summary-card__description">
            <strong>ROL</strong> é valor monetário (R$) com IPI. Matriz usa filial
            01 e comparativo de filial 02. Use dia, semana, mês ou ano no gráfico
            de evolução. A taxa de conversão e os clientes novos respeitam o
            filtro de filial quando informado.
          </p>
        </article>
      </section>
    </div>
  );
}
