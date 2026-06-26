import { useMemo } from "react";
import {
  CircleGauge,
  HandCoins,
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
import { buildKpiGoalPresentation, formatDashboardMetricValue } from "../utils/goalDisplay";
import { formatBranchFilterLabel } from "../utils/branchClientFilters";
import {
  formatCurrency,
  formatInteger,
} from "../utils/format";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";

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
    title: "Giro de estoque",
    description: "Giro em meses, contexto de estoque e CPV do período.",
    href: SUPPLIES_ROUTES.inventoryTurnover,
  },
  {
    title: "Economia em negociações",
    description: "Economia em compras por filial (planilha IDD Suprimentos).",
    href: SUPPLIES_ROUTES.negotiationSavings,
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
    competence,
    branches,
    location,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    setLocation,
    periodParams,
    stockParams,
    filterState,
  } = filters;

  const { cpv, otd, stockValue, inventoryTurnover, negotiationSavings, loading, refreshing, requestProgress, error, reload } =
    useSuppliesDashboard({ periodParams, stockParams });

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = formatBranchFilterLabel(branches);
  const locationLabel = location ? `Local ${location}` : "Todas as localizações";
  const isBusy = loading || refreshing;
  const hasData =
    cpv !== null ||
    otd !== null ||
    stockValue !== null ||
    inventoryTurnover !== null ||
    negotiationSavings !== null;

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        currentPath={pathname ?? SUPPLIES_ROUTES.home}
        filterState={filterState}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        location={location}
        onCompetenceChange={setCompetence}
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
        hasData={hasData}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando dashboard de suprimentos"
        refreshDescription="Recalculando CPV, OTD, estoque, giro e economia em negociações com os filtros selecionados."
      />
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="CPV total"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.cpvTotal}
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
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.cpvRol}
          value={formatDashboardMetricValue(
            cpv?.summary.cpv_percentage,
            cpv?.summary,
          )}
          {...buildKpiGoalPresentation(
            `ROL ${formatCurrency(cpv?.summary.rol_with_ipi)}`,
            cpv?.summary,
            undefined,
            { realizedValue: cpv?.summary.cpv_percentage },
          )}
          icon={<Percent size={22} />}
          loading={isBusy && !cpv}
        />
        <KpiCard
          title="OTD compras"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.otdPurchases}
          value={formatDashboardMetricValue(
            otd?.summary.otd_percentage,
            otd?.summary,
          )}
          {...buildKpiGoalPresentation(
            `${formatInteger(otd?.summary.on_time_lines)} / ${formatInteger(otd?.summary.total_lines)} linhas`,
            otd?.summary,
            undefined,
            { realizedValue: otd?.summary.otd_percentage },
          )}
          icon={<CircleGauge size={22} />}
          loading={isBusy && !otd}
        />
        <KpiCard
          title="Valor de estoque"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.stockValue}
          value={formatDashboardMetricValue(
            stockValue?.summary.total_stock_value,
            stockValue?.summary,
          )}
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
          title="Giro de estoque"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.turnoverTimes}
          value={formatDashboardMetricValue(
            inventoryTurnover?.summary.inventory_turnover_times,
            inventoryTurnover?.summary,
          )}
          {...buildKpiGoalPresentation(
            periodLabel,
            inventoryTurnover?.summary,
            undefined,
            { realizedValue: inventoryTurnover?.summary.inventory_turnover_times },
          )}
          icon={<Package size={22} />}
          loading={isBusy && !inventoryTurnover}
        />
        <KpiCard
          title="Economia em negociações"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.negotiationSavings}
          value={formatDashboardMetricValue(
            negotiationSavings?.summary.total_savings ??
              negotiationSavings?.total_savings,
            negotiationSavings?.summary,
          )}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${periodLabel}`,
            negotiationSavings?.summary,
            undefined,
            {
              realizedValue:
                negotiationSavings?.summary.total_savings ??
                negotiationSavings?.total_savings,
            },
          )}
          icon={<HandCoins size={22} />}
          loading={isBusy && !negotiationSavings}
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