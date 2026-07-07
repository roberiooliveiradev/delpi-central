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
import {
  buildKpiGoalPresentation,
  buildKpiGoalPresentationWithBranchIdd,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { formatBranchFilterLabel, resolveApiBranch } from "../utils/branchClientFilters";
import {
  formatCurrency,
  formatInteger,
} from "../utils/format";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  SuppliesExportButtons,
  buildDashboardExportContext,
} from "../export";

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
    description: "Saldo por unidade, localização e produtos com maior valor.",
    href: SUPPLIES_ROUTES.stock,
  },
  {
    title: "Giro de estoque",
    description: "Giro em meses, contexto de estoque e CPV do período.",
    href: SUPPLIES_ROUTES.inventoryTurnover,
  },
  {
    title: "Economia em negociações",
    description: "Economia em compras por unidade (planilha IDD Suprimentos).",
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

  const { cpv, otd, stockValue, inventoryTurnover, negotiationSavings, cpvBranches, otdBranches, stockValueBranches, inventoryTurnoverBranches, negotiationSavingsBranches, loading, refreshing, requestProgress, error, reload } =
    useSuppliesDashboard({ periodParams, stockParams });

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = formatBranchFilterLabel(branches);
  const activeApiBranch = resolveApiBranch(branches);
  const locationLabel = location ? `Local ${location}` : "Todas as localizações";
  const isBusy = loading || refreshing;
  const hasData =
    cpv !== null ||
    otd !== null ||
    stockValue !== null ||
    inventoryTurnover !== null ||
    negotiationSavings !== null;

  const kpiExportRows = useMemo(
    () => [
      {
        indicador: "CPV total",
        valor: formatCurrency(cpv?.summary.cpv_total),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "CPV / ROL",
        valor: formatDashboardMetricValue(
          cpv?.summary.cpv_percentage,
          cpv?.summary,
        ),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "OTD compras",
        valor: formatDashboardMetricValue(
          otd?.summary.otd_percentage,
          otd?.summary,
        ),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "Valor de estoque",
        valor: formatDashboardMetricValue(
          stockValue?.summary.total_stock_value,
          stockValue?.summary,
        ),
        contexto: `${branchLabel} · ${locationLabel}`,
      },
      {
        indicador: "Giro de estoque",
        valor: formatDashboardMetricValue(
          inventoryTurnover?.summary.inventory_turnover_times,
          inventoryTurnover?.summary,
        ),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
      {
        indicador: "Economia em negociações",
        valor: formatDashboardMetricValue(
          negotiationSavings?.summary.total_savings ??
            negotiationSavings?.total_savings,
          negotiationSavings?.summary,
        ),
        contexto: `${branchLabel} · ${periodLabel}`,
      },
    ],
    [
      branchLabel,
      cpv?.summary,
      inventoryTurnover?.summary,
      locationLabel,
      negotiationSavings,
      otd?.summary,
      periodLabel,
      stockValue?.summary,
    ],
  );

  const dashboardExportContext = useMemo(
    () =>
      buildDashboardExportContext(
        {
          documentTitle: "dashboard-suprimentos",
          periodLabel,
          scopeLabel: `${branchLabel} · ${locationLabel}`,
        },
        kpiExportRows,
      ),
    [branchLabel, kpiExportRows, locationLabel, periodLabel],
  );

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
        exportActions={
          <SuppliesExportButtons
            variant="dashboard"
            context={dashboardExportContext}
            disabled={loading && !hasData}
          />
        }
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
          loading={isBusy}
        />
        <KpiCard
          title="CPV / ROL"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.cpvRol}
          value={formatDashboardMetricValue(
            cpv?.summary.cpv_percentage,
            cpv?.summary,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            `ROL ${formatCurrency(cpv?.summary.rol_with_ipi)}`,
            cpv?.summary,
            {
              realizedValue: cpv?.summary.cpv_percentage,
              activeBranch: activeApiBranch,
              branches: cpvBranches,
            },
          )}
          icon={<Percent size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="OTD compras"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.otdPurchases}
          value={formatDashboardMetricValue(
            otd?.summary.otd_percentage,
            otd?.summary,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            `${formatInteger(otd?.summary.on_time_lines)} / ${formatInteger(otd?.summary.total_lines)} linhas`,
            otd?.summary,
            {
              realizedValue: otd?.summary.otd_percentage,
              activeBranch: activeApiBranch,
              branches: otdBranches,
            },
          )}
          icon={<CircleGauge size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Valor de estoque"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.stockValue}
          value={formatDashboardMetricValue(
            stockValue?.summary.total_stock_value,
            stockValue?.summary,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            `${branchLabel} · ${locationLabel}`,
            stockValue?.summary,
            {
              realizedValue: stockValue?.summary.total_stock_value,
              activeBranch: activeApiBranch,
              branches: stockValueBranches,
            },
          )}
          icon={<Warehouse size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Giro de estoque"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.turnoverTimes}
          value={formatDashboardMetricValue(
            inventoryTurnover?.summary.inventory_turnover_times,
            inventoryTurnover?.summary,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            periodLabel,
            inventoryTurnover?.summary,
            {
              realizedValue: inventoryTurnover?.summary.inventory_turnover_times,
              activeBranch: activeApiBranch,
              branches: inventoryTurnoverBranches,
            },
          )}
          icon={<Package size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Economia em negociações"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.negotiationSavings}
          value={formatDashboardMetricValue(
            negotiationSavings?.summary.total_savings ??
              negotiationSavings?.total_savings,
            negotiationSavings?.summary,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            `${branchLabel} · ${periodLabel}`,
            negotiationSavings?.summary,
            {
              realizedValue:
                negotiationSavings?.summary.total_savings ??
                negotiationSavings?.total_savings,
              activeBranch: activeApiBranch,
              branches: negotiationSavingsBranches,
            },
          )}
          icon={<HandCoins size={22} />}
          loading={isBusy}
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