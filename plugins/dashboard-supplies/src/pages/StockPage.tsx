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
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { StockContextCard } from "../components/StockContextCard";
import { SuppliesStatusAlerts } from "../components/SuppliesStatusAlerts";
import { CHART_COLORS } from "../constants/chartColors";
import { SUPPLIES_ROUTES } from "../constants/routes";
import { useSuppliesFilters } from "../hooks/useSuppliesFilters";
import { useSuppliesResource } from "../hooks/useSuppliesResource";
import type { StockTopProduct, StockValueByLocation } from "../types/supplies";
import { formatChartCurrencyAxis } from "../utils/chartHelpers";
import { formatOperationalUnitCode } from "../utils/operationalUnitLabels";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
} from "../utils/format";
import { buildKpiGoalPresentation, formatDashboardMetricValue } from "../utils/goalDisplay";
import { formatBranchFilterLabel } from "../utils/branchClientFilters";
import { formatProtheusDateHuman } from "../utils/dates";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";
import { STATE_BOX_EMPTY } from "../ui/stateChrome";

const CHART_HEIGHT = 320;

type StockPageProps = { pathname?: string };

export function StockPage({ pathname }: StockPageProps) {
  const {
    dateStart,
    dateEnd,
    competence,
    branches,
    location,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
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

  const isOfficialClosure =
    data?.estimation?.method === "sb9_closure_on_end_date" ||
    data?.estimation?.stock_method_resolved === "official_closure";

  const isRegisterSnapshot =
    data?.estimation?.method === "sb2_register_snapshot" ||
    data?.estimation?.stock_method_resolved === "register_snapshot";

  const branchLabel = formatBranchFilterLabel(branches);
  const locationLabel = location ? `Local ${location}` : "Todas";

  const byLocationChart = useMemo(
    () =>
      (data?.by_location ?? [])
        .filter((item) => Number(item.total_stock_value ?? 0) > 0)
        .map((item) => {
          const raw = item.location ?? "—";
          return {
            name: raw.length > 20 ? `${raw.slice(0, 20)}…` : raw,
            value: Number(item.total_stock_value ?? 0),
          };
        }),
    [data?.by_location]
  );

  const byLocationChartHeight = Math.max(280, byLocationChart.length * 40 + 48);

  const byBranchChart = useMemo(
    () =>
      (data?.by_branch ?? []).map((item) => ({
        name: formatOperationalUnitCode(item.branch),
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

  const estimationSubtitle = hasHistoricalPeriod
    ? isOfficialClosure
      ? `Fechamento oficial SB9 em ${formatProtheusDateHuman(data?.estimation?.end_date)}`
      : isRegisterSnapshot
        ? "Snapshot SB2 alinhado ao Registro de Inventário (MATR460)"
        : data?.estimation?.enabled
          ? "Estimativa Kardex SB9+SD3 (modo analítico)"
          : "Período histórico — aguardando dados"
    : "Posição atual por unidade e localização (SB2)";

  const primaryKpiTitle = isRegisterSnapshot ? "EM estoque (SB2)" : "Valor total";

  const isBusy = loading || refreshing;

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        title="Estoque"
        subtitle={estimationSubtitle}
        currentPath={pathname ?? SUPPLIES_ROUTES.stock}
        filterState={filterState}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        location={location}
        showLocationFilter
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onLocationChange={setLocation}
        onRefresh={reload}
        refreshing={refreshing}
      />
      <StockContextCard
        dateStart={dateStart}
        dateEnd={dateEnd}
        branchLabel={branchLabel}
        locationLabel={locationLabel}
        hasHistoricalPeriod={hasHistoricalPeriod}
        estimation={data?.estimation}
        isOfficialClosure={isOfficialClosure}
        isRegisterSnapshot={isRegisterSnapshot}
        byBranch={data?.by_branch}
      />
      <SuppliesStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={data !== null}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando estoque"
      />

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title={primaryKpiTitle}
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.stockValue}
          value={formatDashboardMetricValue(
            data?.summary.total_stock_value,
            data?.summary,
          )}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${locationLabel}`,
            data?.summary,
            undefined,
            { realizedValue: data?.summary.total_stock_value },
          )}
          icon={<Warehouse size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Quantidade"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.stockQuantity}
          value={formatDecimal(data?.summary.total_stock_quantity, 0)}
          subtitle={`${formatInteger(data?.summary.total_products)} produtos`}
          icon={<Warehouse size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Localizações"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.locations}
          value={formatInteger(data?.summary.total_locations)}
          subtitle={`${formatInteger(data?.summary.total_records)} registros`}
          icon={<Warehouse size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Valor médio / unidade"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.avgUnitValue}
          value={formatCurrency(data?.summary.average_unit_value)}
          subtitle="Custo unitário médio"
          icon={<Warehouse size={22} />}
          loading={isBusy}
        />
      </section>

      <section className="ds-charts-grid">
        <ChartCard title="Estoque por localização">
          {byLocationChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={byLocationChartHeight}>
              <BarChart data={byLocationChart} layout="vertical" margin={{ left: 4, right: 16, top: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={formatChartCurrencyAxis} />
                <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" name="Valor" radius={[0, 8, 8, 0]} maxBarSize={32}>
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
            <div className={STATE_BOX_EMPTY}>Sem saldo por localização no período.</div>
          )}
        </ChartCard>

        <ChartCard title="Estoque por unidade">
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
            <div className={STATE_BOX_EMPTY}>Sem saldo por unidade.</div>
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