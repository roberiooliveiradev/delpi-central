import { useMemo } from "react";
import {
  CircleGauge,
  Package,
  Percent,
  TrendingUp,
  Warehouse,
} from "lucide-react";

import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { ModuleShortcut } from "../components/ModuleShortcut";
import { SuppliesStatusAlerts } from "../components/SuppliesStatusAlerts";
import { SUPPLIES_ROUTES } from "../constants/routes";
import { useSuppliesDashboard } from "../hooks/useSuppliesDashboard";
import { useSuppliesFilters } from "../hooks/useSuppliesFilters";
import { formatPeriodLabel } from "../utils/dates";
import { buildKpiGoalPresentation } from "../utils/goalDisplay";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
  formatPercent,
} from "../utils/format";

const SHORTCUTS = [
  {
    title: "CPV detalhado",
    description: "CFOP, TM, produtos e documentos com maior custo.",
    href: SUPPLIES_ROUTES.cpv,
  },
  {
    title: "OTD compras",
    description: "Série mensal, fornecedores críticos e entregas em atraso.",
    href: SUPPLIES_ROUTES.otd,
  },
  {
    title: "Estoque",
    description: "Saldo por filial, localização e produtos com maior valor.",
    href: SUPPLIES_ROUTES.stock,
  },
  {
    title: "Giro IDD",
    description: "Giro em meses, contexto de estoque e CPV do período.",
    href: SUPPLIES_ROUTES.inventoryTurnover,
  },
] as const;

type DashboardSuppliesPageProps = {
  pathname?: string;
};

export function DashboardSuppliesPage({ pathname }: DashboardSuppliesPageProps) {
  const filters = useSuppliesFilters();
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
    stockParams,
    filterState,
  } = filters;

  const { cpv, otd, stockValue, inventoryTurnover, loading, refreshing, requestProgress, error, reload } =
    useSuppliesDashboard({ periodParams, stockParams });

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = branch ? `Filial ${branch}` : "Consolidado";
  const locationLabel = location ? `Local ${location}` : "Todas as localizações";
  const isBusy = loading || refreshing;
  const hasData =
    cpv !== null || otd !== null || stockValue !== null || inventoryTurnover !== null;

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        currentPath={pathname ?? SUPPLIES_ROUTES.home}
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
      <SuppliesStatusAlerts
        error={error}
        loading={loading}
        hasData={hasData}
        requestProgress={requestProgress}
        onRetry={reload}
      />
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="CPV total"
          value={formatCurrency(cpv?.summary.cpv_total)}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${periodLabel}`,
            cpv?.summary,
            undefined,
            { showGoal: false },
          )}
          icon={<TrendingUp size={22} />}
          loading={isBusy && !cpv}
        />
        <KpiCard
          title="CPV / ROL"
          value={formatPercent(cpv?.summary.cpv_percentage)}
          {...buildKpiGoalPresentation(
            `ROL ${formatCurrency(cpv?.summary.rol_with_ipi)}`,
            cpv?.summary,
            formatPercent,
            { realizedValue: cpv?.summary.cpv_percentage },
          )}
          icon={<Percent size={22} />}
          loading={isBusy && !cpv}
        />
        <KpiCard
          title="OTD compras"
          value={formatPercent(otd?.summary.otd_percentage)}
          {...buildKpiGoalPresentation(
            `${formatInteger(otd?.summary.on_time_lines)} / ${formatInteger(otd?.summary.total_lines)} linhas`,
            otd?.summary,
            formatPercent,
            { realizedValue: otd?.summary.otd_percentage },
          )}
          icon={<CircleGauge size={22} />}
          loading={isBusy && !otd}
        />
        <KpiCard
          title="Valor de estoque"
          value={formatCurrency(stockValue?.summary.total_stock_value)}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${locationLabel}`,
            stockValue?.summary,
            undefined,
            { realizedValue: stockValue?.summary.total_stock_value },
          )}
          icon={<Warehouse size={22} />}
          loading={isBusy && !stockValue}
        />
        <KpiCard
          title="Giro IDD (meses)"
          value={formatDecimal(inventoryTurnover?.summary.inventory_turnover_months, 2)}
          {...buildKpiGoalPresentation(
            periodLabel,
            inventoryTurnover?.summary,
            (v) => formatDecimal(v, 2),
            { realizedValue: inventoryTurnover?.summary.inventory_turnover_months },
          )}
          icon={<Package size={22} />}
          loading={isBusy && !inventoryTurnover}
        />
      </section>
      <section className="ds-shortcuts-grid">
        {SHORTCUTS.map((item) => (
          <ModuleShortcut
            key={item.href}
            title={item.title}
            description={item.description}
            href={item.href}
            filterState={filterState}
          />
        ))}
      </section>
    </div>
  );
}
