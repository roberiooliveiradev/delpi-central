import { useMemo } from "react";
import { Package, Percent, TrendingUp, Warehouse } from "lucide-react";

import { getInventoryTurnover } from "../api/suppliesApi";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { SuppliesStatusAlerts } from "../components/SuppliesStatusAlerts";
import { TurnoverContextCard } from "../components/TurnoverContextCard";
import { SUPPLIES_ROUTES } from "../constants/routes";
import { useSuppliesFilters } from "../hooks/useSuppliesFilters";
import { useSuppliesResource } from "../hooks/useSuppliesResource";
import { formatPeriodLabel } from "../utils/dates";
import { formatCurrency, formatDecimal } from "../utils/format";
import { buildKpiGoalPresentation, formatDashboardMetricValue } from "../utils/goalDisplay";
import { formatBranchFilterLabel } from "../utils/branchClientFilters";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";

type InventoryTurnoverPageProps = { pathname?: string };

const CALC_MODE_SUBTITLE: Record<string, string> = {
  closed_month: "Mês fechado — estoque ÷ CPV médio mensal",
  full_month_range: "Meses completos — estoque ÷ CPV médio mensal",
  partial_period_monthlyized: "Período parcial mensalizado — estoque ÷ CPV médio mensal",
};

export function InventoryTurnoverPage({ pathname }: InventoryTurnoverPageProps) {
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

  const branchLabel = formatBranchFilterLabel(branches);
  const locationLabel = location ? `Local ${location}` : "Todas";

  const isOfficialClosure =
    data?.stock_estimation?.method === "sb9_closure_on_end_date" ||
    data?.stock_estimation?.stock_method_resolved === "official_closure";

  const isRegisterSnapshot =
    data?.stock_estimation?.method === "sb2_register_snapshot" ||
    data?.stock_estimation?.stock_method_resolved === "register_snapshot";

  const subtitle =
    (data?.calculation_context.calculation_mode &&
      CALC_MODE_SUBTITLE[data.calculation_context.calculation_mode]) ||
    "Estoque ÷ CPV médio mensal — em meses";

  const isBusy = loading || refreshing;

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        title="Giro de estoque"
        subtitle={subtitle}
        currentPath={pathname ?? SUPPLIES_ROUTES.inventoryTurnover}
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
      <TurnoverContextCard
        dateStart={dateStart}
        dateEnd={dateEnd}
        branchLabel={branchLabel}
        locationLabel={locationLabel}
        data={data}
        isOfficialClosure={isOfficialClosure}
        isRegisterSnapshot={isRegisterSnapshot}
      />
      <SuppliesStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={data !== null}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando giro de estoque"
      />

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Giro (meses)"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.turnoverMonths}
          value={formatDashboardMetricValue(
            data?.summary.inventory_turnover_months,
            data?.summary,
          )}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${locationLabel} · ${periodLabel}`,
            data?.summary,
            undefined,
            { realizedValue: data?.summary.inventory_turnover_months },
          )}
          icon={<Package size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Giro (vezes)"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.turnoverTimes}
          value={formatDecimal(data?.summary.inventory_turnover_times, 2)}
          subtitle="CPV total ÷ estoque"
          icon={<TrendingUp size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Estoque"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.stockValue}
          value={formatDashboardMetricValue(
            data?.summary.total_stock_value,
            data?.stock_context,
          )}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${locationLabel}`,
            data?.stock_context,
            undefined,
            { realizedValue: data?.summary.total_stock_value },
          )}
          icon={<Warehouse size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="CPV médio mensal"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.cpvTotal}
          value={formatCurrency(data?.summary.cpv_average_monthly)}
          subtitle={periodLabel}
          icon={<Percent size={22} />}
          loading={isBusy && !data}
        />
      </section>
    </div>
  );
}