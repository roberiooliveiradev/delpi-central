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
import { Warehouse } from "lucide-react";

import { getStockValue } from "../api/suppliesApi";
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
import type { StockTopProduct, StockValueByLocation } from "../types/supplies";
import { formatChartCurrencyAxis } from "../utils/chartHelpers";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
} from "../utils/format";
import { buildKpiGoalPresentation } from "../utils/goalDisplay";

const CHART_HEIGHT = 320;

type StockPageProps = { pathname?: string };

export function StockPage({ pathname }: StockPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    location,
    setDateStart,
    setDateEnd,
    setBranch,
    setLocation,
    stockParams,
    filterState,
  } = useSuppliesFilters();

  const { data, loading, refreshing, requestProgress, error, reload } = useSuppliesResource(
    (signal) => getStockValue(stockParams, signal),
    [
      stockParams.branch,
      stockParams.location,
      stockParams.start_date,
      stockParams.end_date,
    ]
  );

  const hasHistoricalPeriod = Boolean(
    stockParams.start_date && stockParams.end_date
  );
  const isEstimatedStock = Boolean(data?.estimation?.enabled);

  const branchLabel = branch ? `Filial ${branch}` : "Consolidado";
  const locationLabel = location ? `Local ${location}` : "Todas";

  const byLocationChart = useMemo(
    () =>
      (data?.by_location ?? [])
        .filter((item) => Number(item.total_stock_value ?? 0) > 0)
        .map((item) => ({
          name: item.location ?? "—",
          value: Number(item.total_stock_value ?? 0),
        })),
    [data?.by_location]
  );

  const byBranchChart = useMemo(
    () =>
      (data?.by_branch ?? []).map((item) => ({
        name: item.branch ?? "—",
        value: Number(item.total_stock_value ?? 0),
      })),
    [data?.by_branch]
  );

  const locationColumns = useMemo<DataTableColumn<StockValueByLocation>[]>(
    () => [
      { key: "loc", header: "Localização", render: (row) => row.location ?? "—" },
      {
        key: "value",
        header: "Valor (R$)",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.total_stock_value),
      },
      {
        key: "qty",
        header: "Quantidade",
        className: "ds-table__col--numeric",
        render: (row) => formatDecimal(row.total_stock_quantity, 2),
      },
    ],
    []
  );

  const productColumns = useMemo<DataTableColumn<StockTopProduct>[]>(
    () => [
      {
        key: "product",
        header: "Produto",
        className: "ds-table__col--wide",
        render: (row) =>
          `${row.product_code ?? "—"} — ${row.product_description ?? ""}`,
      },
      { key: "loc", header: "Local", render: (row) => row.location ?? "—" },
      {
        key: "value",
        header: "Valor (R$)",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.total_stock_value),
      },
      {
        key: "qty",
        header: "Qtd",
        className: "ds-table__col--numeric",
        render: (row) => formatDecimal(row.total_stock_quantity, 2),
      },
    ],
    []
  );

  const isBusy = loading || refreshing;

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        title="Estoque"
        subtitle={
          hasHistoricalPeriod
            ? "Valor estimado no período (SB9 + movimentações SD3)"
            : "Posição atual por filial e localização (SB2)"
        }
        currentPath={pathname ?? SUPPLIES_ROUTES.stock}
        filterState={filterState}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        location={location}
        showLocationFilter
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onLocationChange={setLocation}
        onRefresh={reload}
        refreshing={refreshing}
      />
      <DataSourceBanner />
      {isEstimatedStock ? (
        <div className="ds-state-box" role="status">
          {data?.estimation?.note ??
            "Valor estimado; não substitui fechamento oficial da SB9."}
        </div>
      ) : null}
      <SuppliesStatusAlerts
        error={error}
        loading={loading}
        hasData={data !== null}
        requestProgress={requestProgress}
        onRetry={reload}
      />

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Valor total"
          value={formatCurrency(data?.summary.total_stock_value)}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${locationLabel}`,
            data?.summary,
            undefined,
            { realizedValue: data?.summary.total_stock_value },
          )}
          icon={<Warehouse size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Quantidade"
          value={formatDecimal(data?.summary.total_stock_quantity, 0)}
          subtitle={`${formatInteger(data?.summary.total_products)} produtos`}
          icon={<Warehouse size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Localizações"
          value={formatInteger(data?.summary.total_locations)}
          subtitle={`${formatInteger(data?.summary.total_records)} registros`}
          icon={<Warehouse size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Valor médio / unidade"
          value={formatCurrency(data?.summary.average_unit_value)}
          subtitle="Custo unitário médio"
          icon={<Warehouse size={22} />}
          loading={isBusy && !data}
        />
      </section>

      <section className="ds-charts-grid">
        <ChartCard title="Estoque por localização">
          {byLocationChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={byLocationChart} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={formatChartCurrencyAxis} />
                <YAxis type="category" dataKey="name" width={72} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" name="Valor">
                  {byLocationChart.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Sem saldo por localização no período.</div>
          )}
        </ChartCard>

        <ChartCard title="Estoque por filial">
          {byBranchChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={byBranchChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis tickFormatter={formatChartCurrencyAxis} width={72} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" name="Valor" fill={CHART_COLORS[0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Sem saldo por filial.</div>
          )}
        </ChartCard>
      </section>

      <DataTableSection
        title="Saldo por localização"
        columns={locationColumns}
        rows={data?.by_location ?? []}
        rowKey={(row) => row.location ?? "loc"}
        loading={loading && !(data?.by_location?.length)}
        refreshing={refreshing}
        searchPlaceholder="Buscar localização…"
      />

      <DataTableSection
        title="Top produtos por valor em estoque"
        columns={productColumns}
        rows={data?.top_products ?? []}
        rowKey={(row) => `${row.product_code}-${row.location}`}
        loading={loading && !(data?.top_products?.length)}
        refreshing={refreshing}
        searchPlaceholder="Buscar produto, localização…"
        getSearchText={(row) =>
          `${row.product_code ?? ""} ${row.product_description ?? ""} ${row.location ?? ""}`
        }
      />
    </div>
  );
}
