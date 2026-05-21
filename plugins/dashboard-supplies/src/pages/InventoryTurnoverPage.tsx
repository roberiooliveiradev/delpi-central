import { useMemo } from "react";
import { Package, Percent, TrendingUp, Warehouse } from "lucide-react";

import { getInventoryTurnover } from "../api/suppliesApi";
import { ChartCard } from "../components/ChartCard";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { SuppliesStatusAlerts } from "../components/SuppliesStatusAlerts";
import { SUPPLIES_ROUTES } from "../constants/routes";
import { useSuppliesFilters } from "../hooks/useSuppliesFilters";
import { useSuppliesResource } from "../hooks/useSuppliesResource";
import { formatPeriodLabel } from "../utils/dates";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
} from "../utils/format";

type MetricRow = { label: string; value: string };

type InventoryTurnoverPageProps = { pathname?: string };

export function InventoryTurnoverPage({ pathname }: InventoryTurnoverPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    location,
    setDateStart,
    setDateEnd,
    setBranch,
    setLocation,
    periodParams,
    filterState,
  } = useSuppliesFilters();

  const { data, loading, refreshing, requestProgress, error, reload } = useSuppliesResource(
    (signal) => getInventoryTurnover(periodParams, signal),
    [
      periodParams.branch,
      periodParams.end_date,
      periodParams.location,
      periodParams.start_date,
    ]
  );

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const branchLabel = branch ? `Filial ${branch}` : "Consolidado";
  const locationLabel = location ? `Local ${location}` : "Todas";

  const stockRows = useMemo<MetricRow[]>(
    () =>
      data
        ? [
            {
              label: "Valor em estoque",
              value: formatCurrency(data.stock_context.total_stock_value),
            },
            {
              label: "Quantidade",
              value: formatDecimal(data.stock_context.total_stock_quantity, 0),
            },
            {
              label: "Produtos",
              value: formatInteger(data.stock_context.total_products),
            },
            {
              label: "Localizações",
              value: formatInteger(data.stock_context.total_locations),
            },
            {
              label: "Valor médio / unidade",
              value: formatCurrency(data.stock_context.average_unit_value),
            },
          ]
        : [],
    [data]
  );

  const cpvRows = useMemo<MetricRow[]>(
    () =>
      data
        ? [
            {
              label: "CPV total no período",
              value: formatCurrency(data.cpv_context.cpv_total),
            },
            {
              label: "CPV médio mensal",
              value: formatCurrency(data.cpv_context.cpv_average_monthly),
            },
            {
              label: "Movimentos",
              value: formatInteger(data.cpv_context.total_movements),
            },
            {
              label: "Quantidade movimentada",
              value: formatDecimal(data.cpv_context.total_quantity, 0),
            },
          ]
        : [],
    [data]
  );

  const contextColumns = useMemo<DataTableColumn<MetricRow>[]>(
    () => [
      { key: "label", header: "Indicador", render: (row) => row.label },
      {
        key: "value",
        header: "Valor",
        className: "ds-table__col--numeric",
        render: (row) => row.value,
      },
    ],
    []
  );

  const calcModeLabel: Record<string, string> = {
    closed_month: "Mês fechado",
    full_month_range: "Intervalo de meses completos",
    partial_period_monthlyized: "Período parcial (mensalizado)",
  };

  const isBusy = loading || refreshing;
  const iddValid = data?.calculation_context.idd_period_valid;

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        title="Giro de estoque (IDD)"
        subtitle="Estoque ÷ CPV médio mensal — em meses"
        currentPath={pathname ?? SUPPLIES_ROUTES.inventoryTurnover}
        filterState={filterState}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        location={location}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onLocationChange={setLocation}
        onRefresh={reload}
        refreshing={refreshing}
      />
      <DataSourceBanner />

      {!iddValid && data ? (
        <div className="ds-state ds-state--warning" role="status">
          <p>
            Período parcial para IDD oficial. O cálculo usa CPV mensalizado;
            prefira mês fechado ou intervalo só com meses completos.
          </p>
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
          title="Giro (meses)"
          value={formatDecimal(data?.summary.inventory_turnover_months, 2)}
          subtitle={`${branchLabel} · ${locationLabel} · ${periodLabel}`}
          icon={<Package size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Giro (vezes)"
          value={formatDecimal(data?.summary.inventory_turnover_times, 2)}
          subtitle="CPV total ÷ estoque"
          icon={<TrendingUp size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Estoque"
          value={formatCurrency(data?.summary.total_stock_value)}
          subtitle="Base do numerador"
          icon={<Warehouse size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="CPV médio mensal"
          value={formatCurrency(data?.summary.cpv_average_monthly)}
          subtitle={
            data
              ? calcModeLabel[data.calculation_context.calculation_mode] ??
                data.calculation_context.calculation_mode
              : periodLabel
          }
          icon={<Percent size={22} />}
          loading={isBusy && !data}
        />
      </section>

      <section className="ds-charts-grid ds-charts-grid--single">
        <ChartCard
          title="Contexto do cálculo"
          hint={`Referência: ${data?.calculation_context.period_reference ?? "—"} · Período IDD válido: ${iddValid ? "sim" : "não"}`}
        >
          <div className="ds-metric-pairs">
            <DataTableSection
              title="Estoque"
              columns={contextColumns}
              rows={stockRows}
              rowKey={(row) => `stock-${row.label}`}
              loading={loading && stockRows.length === 0}
              refreshing={refreshing}
              hideSearch
              pageSize={10}
            />
            <DataTableSection
              title="CPV no período"
              columns={contextColumns}
              rows={cpvRows}
              rowKey={(row) => `cpv-${row.label}`}
              loading={loading && cpvRows.length === 0}
              refreshing={refreshing}
              hideSearch
              pageSize={10}
            />
          </div>
        </ChartCard>
      </section>
    </div>
  );
}
