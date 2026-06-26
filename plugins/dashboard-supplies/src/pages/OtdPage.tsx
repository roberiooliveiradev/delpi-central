import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CircleGauge, Truck } from "lucide-react";

import { getOtd } from "../api/suppliesApi";
import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
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
import type { LateDeliveryItem, LateSupplierItem } from "../types/supplies";
import type { ChartGranularity } from "../types/chart";
import { buildOtdTrendSeries } from "../utils/chartMonthlySeries";
import { formatPeriodLabel, formatDisplayDate } from "../utils/dates";
import { suggestGranularity } from "../utils/periodBuckets";
import { buildKpiGoalPresentation, formatDashboardMetricValue } from "../utils/goalDisplay";
import { formatInteger, formatPercent } from "../utils/format";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";

const CHART_HEIGHT = 320;

type OtdPageProps = { pathname?: string };

export function OtdPage({ pathname }: OtdPageProps) {
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

  const [granularity, setGranularity] = useState<ChartGranularity>("month");

  const { data, loading, refreshing, requestProgress, error, reload } = useSuppliesResource(
    (signal) => getOtd(periodParams, signal),
    [periodParams.branch, periodParams.end_date, periodParams.start_date]
  );

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  useEffect(() => {
    const suggested = suggestGranularity(dateStart, dateEnd);
    setGranularity(suggested === "year" ? "year" : "month");
  }, [dateStart, dateEnd]);

  const monthlyChart = useMemo(
    () =>
      buildOtdTrendSeries(
        data?.monthly_breakdown ?? [],
        dateStart,
        dateEnd,
        granularity
      ),
    [data?.monthly_breakdown, dateStart, dateEnd, granularity]
  );

  const otdChartModes: ChartGranularity[] = ["month", "year"];

  const lateSuppliersChart = useMemo(
    () =>
      (data?.top_late_suppliers ?? []).slice(0, 10).map((item) => {
        const raw =
          item.supplier_name ??
          item.supplier ??
          item.supplier_code ??
          "Fornecedor";
        return {
          name: raw.length > 24 ? `${raw.slice(0, 24)}…` : raw,
          value: Number(item.late_lines ?? 0),
        };
      }),
    [data?.top_late_suppliers]
  );

  const lateSuppliersChartHeight = Math.max(280, lateSuppliersChart.length * 40 + 48);

  const supplierColumns = useMemo<DataTableColumn<LateSupplierItem>[]>(
    () => [
      {
        key: "supplier",
        header: "Fornecedor",
        className: "ds-table__col--wide",
        render: (row) =>
          row.supplier_name ?? row.supplier ?? row.supplier_code ?? "—",
      },
      {
        key: "late",
        header: "Linhas atrasadas",
        className: "ds-table__col--numeric",
        render: (row) => formatInteger(row.late_lines),
      },
      {
        key: "total",
        header: "Total linhas",
        className: "ds-table__col--numeric",
        render: (row) => formatInteger(row.total_lines),
      },
      {
        key: "pct",
        header: "% atraso",
        className: "ds-table__col--numeric",
        render: (row) => formatPercent(row.late_percentage),
      },
    ],
    []
  );

  const deliveryColumns = useMemo<DataTableColumn<LateDeliveryItem>[]>(
    () => [
      {
        key: "supplier",
        header: "Fornecedor",
        className: "ds-table__col--wide",
        render: (row) => row.supplier_name ?? row.supplier_code ?? "—",
      },
      { key: "order", header: "Pedido", render: (row) => row.order_number ?? "—" },
      {
        key: "product",
        header: "Produto",
        className: "ds-table__col--wide",
        render: (row) =>
          `${row.product_code ?? ""} ${row.product_description ?? ""}`.trim() ||
          "—",
      },
      {
        key: "expected",
        header: "Previsto",
        render: (row) => formatDisplayDate(row.expected_delivery_date),
      },
      {
        key: "days",
        header: "Dias",
        className: "ds-table__col--numeric",
        render: (row) => formatInteger(row.days_diff),
      },
    ],
    []
  );

  const isBusy = loading || refreshing;

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        title="OTD — Pontualidade de compras"
        subtitle="Linhas recebidas no prazo versus atrasadas"
        currentPath={pathname ?? SUPPLIES_ROUTES.otd}
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
        refreshTitle="Atualizando OTD de compras"
      />

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="OTD"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.otd}
          value={formatDashboardMetricValue(
            data?.summary.otd_percentage,
            data?.summary,
          )}
          {...buildKpiGoalPresentation(periodLabel, data?.summary, undefined, {
            realizedValue: data?.summary.otd_percentage,
          })}
          icon={<CircleGauge size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Linhas no prazo"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.onTimeLines}
          value={formatInteger(data?.summary.on_time_lines)}
          subtitle={`De ${formatInteger(data?.summary.total_lines)} linhas`}
          icon={<Truck size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Linhas em atraso"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.lateLines}
          value={formatInteger(data?.summary.late_lines)}
          subtitle={formatPercent(data?.summary.late_percentage)}
          icon={<Truck size={22} />}
          loading={isBusy && !data}
        />
      </section>

      <section className="ds-charts-grid">
        <ChartCard title="OTD no período" hint="Evolução da pontualidade (dados mensais da API).">
          <ChartToolbar
            idPrefix="otd-trend"
            granularity={granularity}
            onGranularityChange={setGranularity}
            modes={otdChartModes}
          />
          {monthlyChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <LineChart data={monthlyChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} unit="%" />
                <Tooltip
                  formatter={(value, name) =>
                    name === "otd"
                      ? formatPercent(Number(value))
                      : formatInteger(Number(value))
                  }
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="otd"
                  name="OTD %"
                  stroke={CHART_COLORS[0]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Sem série mensal.</div>
          )}
        </ChartCard>

        <ChartCard title="Fornecedores com mais atrasos">
          {lateSuppliersChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={lateSuppliersChartHeight}>
              <BarChart data={lateSuppliersChart} layout="vertical" margin={{ left: 4, right: 16, top: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" name="Linhas atrasadas" radius={[0, 8, 8, 0]} maxBarSize={32}>
                  {lateSuppliersChart.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Nenhum fornecedor crítico.</div>
          )}
        </ChartCard>
      </section>

      <DataTableSection
        title="Ranking de fornecedores em atraso"
        columns={supplierColumns}
        rows={data?.top_late_suppliers ?? []}
        rowKey={(row) =>
          `${row.supplier_code ?? row.supplier_name ?? "s"}-${row.late_lines}`
        }
        loading={loading && !(data?.top_late_suppliers?.length)}
        refreshing={refreshing}
        searchPlaceholder="Buscar fornecedor…"
      />

      <DataTableSection
        title="Entregas em atraso (amostra)"
        hint="Linhas com DIAS negativo na view de pontualidade."
        columns={deliveryColumns}
        rows={data?.late_deliveries ?? []}
        rowKey={(row) =>
          `${row.order_number}-${row.order_item}-${row.product_code}`
        }
        loading={loading && !(data?.late_deliveries?.length)}
        refreshing={refreshing}
        emptyMessage="Nenhuma entrega em atraso no período."
        searchPlaceholder="Buscar pedido, produto, fornecedor…"
      />
    </div>
  );
}