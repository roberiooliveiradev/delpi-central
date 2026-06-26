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
import { Percent, TrendingUp } from "lucide-react";

import { getCpv } from "../api/suppliesApi";
import { ChartCard } from "../components/ChartCard";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { SuppliesStatusAlerts } from "../components/SuppliesStatusAlerts";
import { CHART_COLORS } from "../constants/chartColors";
import { SUPPLIES_ROUTES } from "../constants/routes";
import { useSuppliesFilters } from "../hooks/useSuppliesFilters";
import { useSuppliesResource } from "../hooks/useSuppliesResource";
import type { CpvBreakdownItem } from "../types/supplies";
import { formatChartCurrencyAxis } from "../utils/chartHelpers";
import { formatPeriodLabel } from "../utils/dates";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
} from "../utils/format";
import { buildKpiGoalPresentation, formatDashboardMetricValue } from "../utils/goalDisplay";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";

const CHART_HEIGHT = 320;

type CpvPageProps = { pathname?: string };

export function CpvPage({ pathname }: CpvPageProps) {
  const {
    dateStart,
    dateEnd,
    branches,
    location,
    setDateStart,
    setDateEnd,
    setBranches,
    setLocation,
    periodParams,
    filterState,
  } = useSuppliesFilters();

  const { data, loading, refreshing, requestProgress, error, reload } = useSuppliesResource(
    (signal) => getCpv(periodParams, signal),
    [periodParams.branch, periodParams.end_date, periodParams.start_date]
  );

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const byCfopChart = useMemo(
    () =>
      (data?.by_cfop ?? []).map((item) => ({
        name: item.cfop ?? "—",
        value: Number(item.cpv_total ?? 0),
      })),
    [data?.by_cfop]
  );

  const byTmChart = useMemo(
    () =>
      (data?.by_tm ?? []).slice(0, 12).map((item) => {
        const raw = item.tm ?? "—";
        return {
          name: raw.length > 20 ? `${raw.slice(0, 20)}…` : raw,
          value: Number(item.cpv_total ?? 0),
        };
      }),
    [data?.by_tm]
  );

  const byTmChartHeight = Math.max(280, byTmChart.length * 40 + 48);

  const productColumns = useMemo<DataTableColumn<CpvBreakdownItem>[]>(
    () => [
      {
        key: "product",
        header: "Produto",
        className: "ds-table__col--wide",
        render: (row) =>
          `${row.product_code ?? "—"} — ${row.product_description ?? ""}`,
      },
      {
        key: "qty",
        header: "Quantidade",
        className: "ds-table__col--numeric",
        render: (row) => formatDecimal(row.total_quantity, 2),
      },
      {
        key: "cpv",
        header: "CPV (R$)",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.cpv_total),
      },
    ],
    []
  );

  const cfopColumns = useMemo<DataTableColumn<CpvBreakdownItem>[]>(
    () => [
      { key: "cfop", header: "CFOP", render: (row) => row.cfop ?? "—" },
      {
        key: "mov",
        header: "Movimentos",
        className: "ds-table__col--numeric",
        render: (row) => formatInteger(row.total_movements),
      },
      {
        key: "cpv",
        header: "CPV (R$)",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.cpv_total),
      },
    ],
    []
  );

  const isBusy = loading || refreshing;

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        title="CPV — Custo de produto vendido"
        subtitle="Movimentos SD3 e participação sobre o ROL"
        currentPath={pathname ?? SUPPLIES_ROUTES.cpv}
        filterState={filterState}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        location={location}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onLocationChange={setLocation}
        onRefresh={reload}
        refreshing={refreshing}
      />
      <DataSourceBanner />
      <SuppliesStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={data !== null}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando CPV"
      />

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="CPV total"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.cpvTotal}
          value={formatCurrency(data?.summary.cpv_total)}
          {...buildKpiGoalPresentation(periodLabel, data?.summary, undefined, {
            showGoal: false,
          })}
          icon={<TrendingUp size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="CPV / ROL"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.cpvRol}
          value={formatDashboardMetricValue(
            data?.summary.cpv_percentage,
            data?.summary,
          )}
          {...buildKpiGoalPresentation(
            `ROL ${formatCurrency(data?.summary.rol_with_ipi)}`,
            data?.summary,
            undefined,
            { realizedValue: data?.summary.cpv_percentage },
          )}
          icon={<Percent size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Movimentos"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.cpvMovements}
          value={formatInteger(data?.summary.total_movements)}
          subtitle={`Qtd ${formatDecimal(data?.summary.total_quantity, 0)}`}
          icon={<TrendingUp size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Custo médio / unidade"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.avgCostPerUnit}
          value={formatCurrency(data?.summary.average_cost_per_unit)}
          subtitle={`Por movimento ${formatCurrency(data?.summary.average_cost_per_movement)}`}
          icon={<Percent size={22} />}
          loading={isBusy && !data}
        />
      </section>

      <section className="ds-charts-grid">
        <ChartCard title="CPV por CFOP" hint="Distribuição por código fiscal.">
          {byCfopChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={byCfopChart} margin={{ left: 8, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
                <YAxis tickFormatter={formatChartCurrencyAxis} width={72} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" name="CPV">
                  {byCfopChart.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Sem dados de CPV por CFOP.</div>
          )}
        </ChartCard>

        <ChartCard title="CPV por TM" hint="Top tipos de movimento (TES).">
          {byTmChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={byTmChartHeight}>
              <BarChart data={byTmChart} layout="vertical" margin={{ left: 4, right: 16, top: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={formatChartCurrencyAxis} />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" name="CPV" fill={CHART_COLORS[1]} radius={[0, 8, 8, 0]} maxBarSize={32} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Sem dados por TM.</div>
          )}
        </ChartCard>
      </section>

      <DataTableSection
        title="Top produtos por CPV"
        columns={productColumns}
        rows={data?.top_products ?? []}
        rowKey={(row) => `${row.product_code ?? "p"}-${row.cpv_total}`}
        loading={loading && !(data?.top_products?.length)}
        refreshing={refreshing}
        emptyMessage="Nenhum produto no período."
        searchPlaceholder="Buscar produto…"
      />

      <DataTableSection
        title="Detalhamento por CFOP"
        columns={cfopColumns}
        rows={data?.by_cfop ?? []}
        rowKey={(row) => row.cfop ?? "cfop"}
        loading={loading && !(data?.by_cfop?.length)}
        refreshing={refreshing}
        searchPlaceholder="Buscar CFOP…"
      />
    </div>
  );
}