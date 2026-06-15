import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  CircleGauge,
  Coins,
  Factory,
  Percent,
  Truck,
  Users,
} from "lucide-react";

import { PRODUCTION_ROUTES } from "../constants/routes";
import { DP_HELP_TOOLTIPS } from "../content/helpTooltips";
import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { OeeEvolutionChart } from "../components/OeeEvolutionChart";
import { OtdEvolutionChart } from "../components/OtdEvolutionChart";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { CHART_COLORS } from "../constants/chartColors";
import { useProductionDashboard } from "../hooks/useProductionDashboard";
import { useAutoRefresh } from "../hooks/useAutoRefresh";
import { useProductionOeeSeries } from "../hooks/useProductionOeeSeries";
import { useProductionOtdSeries } from "../hooks/useProductionOtdSeries";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useProductionFilters } from "../hooks/useProductionFilters";
import type { ChartGranularity } from "../types/chart";
import { downloadOeeSeriesCsv, downloadOtdSeriesCsv } from "../utils/chartSeriesExport";
import { formatPeriodLabel } from "../utils/dates";
import { suggestGranularity } from "../utils/periodBuckets";
import { buildKpiGoalPresentation } from "../utils/goalDisplay";
import { formatPercent } from "../utils/format";

const CHART_HEIGHT = 300;

export function DashboardProductionPage({ pathname }: { pathname?: string }) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useProductionFilters();

  const [granularity, setGranularity] = useState<ChartGranularity>("month");

  const {
    directLabor,
    productionCost,
    depreciation,
    oee,
    otd,
    loading,
    refreshing,
    requestProgress,
    error,
    sectionErrors,
    reload,
  } = useProductionDashboard(apiParams);

  const oeeSeries = useProductionOeeSeries({
    filters: apiParams,
    granularity,
  });

  const otdSeries = useProductionOtdSeries({
    filters: apiParams,
    granularity,
  });

  useEffect(() => {
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const branchLabel = branch
    ? `Filial ${branch}`
    : "Consolidado (média das filiais)";

  const isBusy = loading || refreshing;
  const hasData =
    directLabor !== null ||
    productionCost !== null ||
    depreciation !== null ||
    oee !== null ||
    otd !== null;
  const initialLoadingProgress = useLoadingProgress(loading && !hasData, requestProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing && hasData, requestProgress);

  const refreshAll = useCallback(() => {
    reload();
    oeeSeries.reload();
    otdSeries.reload();
  }, [reload, oeeSeries, otdSeries]);

  useAutoRefresh(refreshAll);

  const comparisonChartData = useMemo(
    () => [
      {
        name: "MO direta",
        value: directLabor?.direct_labor_cost_pct ?? 0,
        key: "directLabor",
      },
      {
        name: "Custo produção",
        value: productionCost?.production_cost_pct ?? 0,
        key: "productionCost",
      },
      {
        name: "Depreciação",
        value: depreciation?.depreciation_pct ?? 0,
        key: "depreciation",
      },
      {
        name: "OEE",
        value: oee?.overall_equipment_effectiveness_pct ?? 0,
        key: "oee",
      },
      {
        name: "OTD",
        value: otd?.on_time_delivery_pct ?? 0,
        key: "otd",
      },
    ],
    [depreciation, directLabor, oee, otd, productionCost]
  );

  const hasChartValues = comparisonChartData.some((item) => item.value > 0);

  const isOeeChartBusy = oeeSeries.loading;
  const isOtdChartBusy = otdSeries.loading;
  const hasOeeChartValues = oeeSeries.points.some(
    (point) =>
      (point.oeeFilial01 != null && point.oeeFilial01 > 0) ||
      (point.oeeFilial02 != null && point.oeeFilial02 > 0)
  );
  const hasOtdChartValues = otdSeries.points.some(
    (point) =>
      (point.otdFilial01 != null && point.otdFilial01 > 0) ||
      (point.otdFilial02 != null && point.otdFilial02 > 0)
  );

  const temporalChartHint = branch
    ? `Clique em um ponto para filtrar o período. Série da filial ${branch}.`
    : "Clique em um ponto para filtrar o período. Séries por filial 01 e 02.";

  const handleTemporalChartDrillDown = useCallback(
    (nextStart: string, nextEnd: string) => {
      setDateStart(nextStart);
      setDateEnd(nextEnd);
    },
    [setDateStart, setDateEnd]
  );

  const handleExportOeeCsv = useCallback(() => {
    downloadOeeSeriesCsv("oee-evolucao.csv", oeeSeries.points);
  }, [oeeSeries.points]);

  const handleExportOtdCsv = useCallback(() => {
    downloadOtdSeriesCsv("otd-evolucao.csv", otdSeries.points);
  }, [otdSeries.points]);

  return (
    <div className="dashboard-production dashboard-page">
      <FilterBar
        currentPath={pathname ?? PRODUCTION_ROUTES.home}
        filterState={filterState}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onRefresh={refreshAll}
        refreshing={refreshing}
      />

      <DataSourceBanner />

      {error ? (
        <div className="dp-state dp-state--error" role="alert">
          <p>{error}</p>
          <button className="dp-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {Object.keys(sectionErrors).length > 0 ? (
        <div className="dp-state dp-state--warning" role="status">
          <p>
            Alguns indicadores não carregaram. Os demais permanecem disponíveis.
          </p>
        </div>
      ) : null}

      {refreshing && hasData ? (
        <LoadingActivityCard
          title="Atualizando indicadores de produção"
          description="Recalculando MO, custos, OEE e OTD com os filtros selecionados."
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando indicadores de produção"
          description="Buscando MO direta, custo de produção, depreciação, OEE e OTD."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <section className="dp-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="MO direta / ROL"
          titleHint={DP_HELP_TOOLTIPS.home.directLabor}
          value={formatPercent(directLabor?.direct_labor_cost_pct)}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${periodLabel}`,
            directLabor,
            formatPercent,
            { realizedValue: directLabor?.direct_labor_cost_pct },
          )}
          icon={<Users size={22} />}
          loading={isBusy && !directLabor}
        />
        <KpiCard
          title="Custo de produção / ROL"
          titleHint={DP_HELP_TOOLTIPS.home.productionCost}
          value={formatPercent(productionCost?.production_cost_pct)}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${periodLabel}`,
            productionCost,
            formatPercent,
            { realizedValue: productionCost?.production_cost_pct },
          )}
          icon={<Coins size={22} />}
          loading={isBusy && !productionCost}
        />
        <KpiCard
          title="Depreciação / ROL"
          titleHint={DP_HELP_TOOLTIPS.home.depreciation}
          value={formatPercent(depreciation?.depreciation_pct)}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${periodLabel}`,
            depreciation,
            formatPercent,
            { realizedValue: depreciation?.depreciation_pct },
          )}
          icon={<Percent size={22} />}
          loading={isBusy && !depreciation}
        />
        <KpiCard
          title="OEE"
          titleHint={DP_HELP_TOOLTIPS.home.oee}
          value={formatPercent(oee?.overall_equipment_effectiveness_pct)}
          {...buildKpiGoalPresentation(
            `TOTVS · ${branchLabel} · ${periodLabel}`,
            oee,
            formatPercent,
            { realizedValue: oee?.overall_equipment_effectiveness_pct },
          )}
          icon={<CircleGauge size={22} />}
          loading={isBusy && !oee}
        />
        <KpiCard
          title="OTD — entrega no prazo"
          titleHint={DP_HELP_TOOLTIPS.home.otd}
          value={formatPercent(otd?.on_time_delivery_pct)}
          {...buildKpiGoalPresentation(
            `TOTVS · ${branchLabel} · ${periodLabel}`,
            otd,
            formatPercent,
            { realizedValue: otd?.on_time_delivery_pct },
          )}
          icon={<Truck size={22} />}
          loading={isBusy && !otd}
        />
      </section>

      <section className="dp-charts-grid">
        <div className="dp-chart-section" aria-busy={isOeeChartBusy}>
          <ChartCard
            title="Evolução do OEE (%)"
            titleHint={DP_HELP_TOOLTIPS.home.oeeEvolution}
            hint={temporalChartHint}
          >
            <ChartToolbar
              idPrefix="oee"
              granularity={granularity}
              onGranularityChange={setGranularity}
              onExportCsv={handleExportOeeCsv}
              exportDisabled={oeeSeries.points.length === 0}
            />

            {oeeSeries.error ? (
              <div className="dp-state dp-state--error" role="alert">
                <p>{oeeSeries.error}</p>
                <button
                  className="dp-primary-btn"
                  type="button"
                  onClick={oeeSeries.reload}
                >
                  Tentar novamente
                </button>
              </div>
            ) : null}

            {!oeeSeries.error &&
            (oeeSeries.points.length > 0 || oeeSeries.loading) ? (
              <OeeEvolutionChart
                data={oeeSeries.points}
                branch={branch || undefined}
                loading={oeeSeries.loading}
                onDrillDown={handleTemporalChartDrillDown}
              />
            ) : null}

            {!oeeSeries.error &&
            oeeSeries.points.length === 0 &&
            !oeeSeries.loading ? (
              <div className="dp-state-box">Sem dados para o gráfico no período.</div>
            ) : null}

            {oeeSeries.truncated ? (
              <p className="dp-chart-card__hint dp-chart-card__hint--below">
                Período limitado aos primeiros 60 intervalos para desempenho.
              </p>
            ) : null}

            {!oeeSeries.error &&
            oeeSeries.points.length > 0 &&
            !hasOeeChartValues &&
            !oeeSeries.loading ? (
              <p className="dp-chart-card__hint dp-chart-card__hint--below">
                Todos os intervalos retornaram OEE zero ou sem apontamento no período.
              </p>
            ) : null}
          </ChartCard>
        </div>

        <div className="dp-chart-section" aria-busy={isOtdChartBusy}>
          <ChartCard
            title="Evolução do OTD (%)"
            titleHint={DP_HELP_TOOLTIPS.home.otdEvolution}
            hint="OPs de PA finalizadas no prazo (C2_DATRF ≤ C2_DATPRF). Clique em um ponto para filtrar o período."
          >
            <ChartToolbar
              idPrefix="otd"
              granularity={granularity}
              onGranularityChange={setGranularity}
              onExportCsv={handleExportOtdCsv}
              exportDisabled={otdSeries.points.length === 0}
            />

            {otdSeries.error ? (
              <div className="dp-state dp-state--error" role="alert">
                <p>{otdSeries.error}</p>
                <button
                  className="dp-primary-btn"
                  type="button"
                  onClick={otdSeries.reload}
                >
                  Tentar novamente
                </button>
              </div>
            ) : null}

            {!otdSeries.error &&
            (otdSeries.points.length > 0 || otdSeries.loading) ? (
              <OtdEvolutionChart
                data={otdSeries.points}
                branch={branch || undefined}
                loading={otdSeries.loading}
                onDrillDown={handleTemporalChartDrillDown}
              />
            ) : null}

            {!otdSeries.error &&
            otdSeries.points.length === 0 &&
            !otdSeries.loading ? (
              <div className="dp-state-box">Sem dados para o gráfico no período.</div>
            ) : null}

            {otdSeries.truncated ? (
              <p className="dp-chart-card__hint dp-chart-card__hint--below">
                Período limitado aos primeiros 60 intervalos para desempenho.
              </p>
            ) : null}

            {!otdSeries.error &&
            otdSeries.points.length > 0 &&
            !hasOtdChartValues &&
            !otdSeries.loading ? (
              <p className="dp-chart-card__hint dp-chart-card__hint--below">
                Todos os intervalos retornaram OTD zero ou sem OP finalizada no período.
              </p>
            ) : null}
          </ChartCard>
        </div>
      </section>

      <section className="dp-chart-section">
        <ChartCard
          title="Comparativo dos indicadores (%)"
          titleHint={DP_HELP_TOOLTIPS.home.comparisonChart}
          hint="Custos sobre ROL e percentuais operacionais no mesmo período."
        >
          {hasChartValues ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={comparisonChartData} layout="vertical" margin={{ left: 4, right: 16, top: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" unit="%" />
                <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(value) =>
                    formatPercent(typeof value === "number" ? value : Number(value))
                  }
                />
                <Bar dataKey="value" name="%">
                  {comparisonChartData.map((entry, index) => (
                    <Cell
                      key={entry.key}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="dp-state-box">Sem dados para o gráfico no período.</div>
          )}
        </ChartCard>
      </section>

      <section className="dp-summary-grid">
        <article className="dp-card">
          <div className="dp-summary-card__header">
            <Factory size={22} aria-hidden />
            <h2 className="dp-summary-card__title">Como ler os indicadores</h2>
          </div>
          <p className="dp-summary-card__description">
            Os três primeiros KPIs são custos médios das planilhas divididos pelo
            ROL (TOTVS) no período. <strong>OEE</strong> é a média de eficiência
            dos apontamentos (gráfico temporal por filial). <strong>OTD</strong> mede ordens de produção
            concluídas no prazo (gráfico temporal por filial).
          </p>
        </article>
      </section>
    </div>
  );
}
