import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Banknote,
  Building2,
  PackageCheck,
  Percent,
  Target,
  TrendingUp,
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
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { ChartToolbar } from "../components/ChartToolbar";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { RolEvolutionChart } from "../components/RolEvolutionChart";
import { TotvsSourceBanner } from "../components/TotvsSourceBanner";
import { CHART_COLORS } from "../constants/chartColors";
import { useCommercialDashboard } from "../hooks/useCommercialDashboard";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useCommercialFilters } from "../hooks/useCommercialFilters";
import { useCommercialRolSeries } from "../hooks/useCommercialRolSeries";
import type { ChartGranularity } from "../types/chart";
import { downloadRolSeriesCsv } from "../utils/chartSeriesExport";
import { formatPeriodLabel } from "../utils/dates";
import { suggestGranularity } from "../utils/periodBuckets";
import { buildKpiGoalPresentation } from "../utils/goalDisplay";
import {
  formatInteger,
  formatCurrency,
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
    salesOrderOtd,
    newBusinessRol,
    loading,
    refreshing,
    requestProgress,
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
  const initialLoadingProgress = useLoadingProgress(loading && !hasData, requestProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing && hasData, requestProgress);

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

      {refreshing && hasData ? (
        <LoadingActivityCard
          title="Atualizando indicadores comerciais"
          description="Recalculando ROL, conversão e OTD com os filtros selecionados."
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando indicadores comerciais"
          description="Buscando ROL, taxa de conversão, OTD e novos negócios no TOTVS."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <section className="dc-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="ROL — Matriz (01)"
          value={formatCurrency(headOfficeRol?.rol)}
          {...buildKpiGoalPresentation(
            periodLabel,
            headOfficeRol,
            formatCurrency,
            { realizedValue: headOfficeRol?.rol },
          )}
          goalScopeBadge={null}
          goalScopeHint={null}
          icon={<Banknote size={22} />}
          loading={isBusy && !headOfficeRol}
        />
        <KpiCard
          title="ROL — Filial (02)"
          value={formatCurrency(branchRol?.rol)}
          {...buildKpiGoalPresentation(
            `Filial 02 · ${periodLabel}`,
            branchRol,
            formatCurrency,
            { realizedValue: branchRol?.rol },
          )}
          goalScopeBadge={null}
          goalScopeHint={null}
          icon={<Building2 size={22} />}
          loading={isBusy && !branchRol}
        />
        <KpiCard
          title="Taxa de conversão"
          value={formatPercent(closingRate?.sales_conversion_rate_pct)}
          {...buildKpiGoalPresentation(
            `${formatInteger(closingRate?.qtd_won)} ganhas / ${formatInteger(closingRate?.qtd_proposals)} propostas · ${periodLabel}`,
            closingRate,
            formatPercent,
            { realizedValue: closingRate?.sales_conversion_rate_pct },
          )}
          icon={<Percent size={22} />}
          loading={isBusy && !closingRate}
        />
        <KpiCard
          title="OTD — pedidos de venda"
          value={formatPercent(salesOrderOtd?.sales_order_otd_pct)}
          {...buildKpiGoalPresentation(
            `${formatInteger(salesOrderOtd?.on_time_lines)} no prazo / ${formatInteger(salesOrderOtd?.total_lines)} linhas · ${periodLabel}`,
            salesOrderOtd,
            formatPercent,
            { realizedValue: salesOrderOtd?.sales_order_otd_pct },
          )}
          icon={<PackageCheck size={22} />}
          loading={isBusy && !salesOrderOtd}
        />
        <KpiCard
          title="% ROL — novos negócios"
          value={formatPercent(newBusinessRol?.new_business_rol_pct)}
          {...buildKpiGoalPresentation(
            `${formatCurrency(newBusinessRol?.new_business_rol)} não-WEG · ${periodLabel}`,
            newBusinessRol,
            formatPercent,
            { realizedValue: newBusinessRol?.new_business_rol_pct },
          )}
          icon={<TrendingUp size={22} />}
          loading={isBusy && !newBusinessRol}
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
              <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
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
            de evolução. Taxa de conversão, OTD e % ROL de novos negócios
            respeitam o filtro de filial quando informado.
          </p>
        </article>
      </section>
    </div>
  );
}
