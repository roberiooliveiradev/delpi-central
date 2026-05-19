import { useMemo } from "react";
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

import { ChartCard } from "../components/ChartCard";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { CHART_COLORS } from "../constants/chartColors";
import { useProductionDashboard } from "../hooks/useProductionDashboard";
import { useProductionFilters } from "../hooks/useProductionFilters";
import { formatPeriodLabel } from "../utils/dates";
import { formatPercent } from "../utils/format";

const CHART_HEIGHT = 300;

export function DashboardProductionPage() {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
  } = useProductionFilters();

  const {
    directLabor,
    productionCost,
    depreciation,
    oee,
    otd,
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  } = useProductionDashboard(apiParams);

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

  return (
    <div className="dashboard-production dashboard-page">
      <FilterBar
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onRefresh={reload}
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

      {loading && !hasData ? (
        <div className="dp-state dp-state--loading" aria-live="polite">
          Carregando indicadores…
        </div>
      ) : null}

      <section className="dp-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="MO direta / ROL"
          value={formatPercent(directLabor?.direct_labor_cost_pct)}
          subtitle={`${branchLabel} · ${periodLabel}`}
          icon={<Users size={22} />}
          loading={isBusy && !directLabor}
        />
        <KpiCard
          title="Custo de produção / ROL"
          value={formatPercent(productionCost?.production_cost_pct)}
          subtitle={`${branchLabel} · ${periodLabel}`}
          icon={<Coins size={22} />}
          loading={isBusy && !productionCost}
        />
        <KpiCard
          title="Depreciação / ROL"
          value={formatPercent(depreciation?.depreciation_pct)}
          subtitle={`${branchLabel} · ${periodLabel}`}
          icon={<Percent size={22} />}
          loading={isBusy && !depreciation}
        />
        <KpiCard
          title="OEE"
          value={formatPercent(oee?.overall_equipment_effectiveness_pct)}
          subtitle={`TOTVS · ${branchLabel} · ${periodLabel}`}
          icon={<CircleGauge size={22} />}
          loading={isBusy && !oee}
        />
        <KpiCard
          title="OTD — entrega no prazo"
          value={formatPercent(otd?.on_time_delivery_pct)}
          subtitle={`TOTVS · ${branchLabel} · ${periodLabel}`}
          icon={<Truck size={22} />}
          loading={isBusy && !otd}
        />
      </section>

      <section className="dp-chart-section">
        <ChartCard
          title="Comparativo dos indicadores (%)"
          hint="Custos sobre ROL e percentuais operacionais no mesmo período."
        >
          {hasChartValues ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={comparisonChartData} layout="vertical" margin={{ left: 12 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" unit="%" />
                <YAxis type="category" dataKey="name" width={120} />
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
            dos apontamentos. <strong>OTD</strong> mede ordens de produção
            concluídas no prazo. Sem filial, a API consolida por média entre
            matriz e filial.
          </p>
        </article>
      </section>
    </div>
  );
}
