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
import { Clock, Landmark, Percent, TrendingUp } from "lucide-react";

import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { ModuleShortcut } from "../components/ModuleShortcut";
import { FinancialStatusAlerts } from "../components/FinancialStatusAlerts";
import { ChartCard } from "../components/ChartCard";
import { CHART_COLORS } from "../constants/chartColors";
import { FINANCIAL_ROUTES } from "../constants/routes";
import { useFinancialDashboard } from "../hooks/useFinancialDashboard";
import { useFinancialFilters } from "../hooks/useFinancialFilters";
import { formatPeriodLabel } from "../utils/dates";
import { buildKpiGoalPresentation } from "../utils/goalDisplay";
import {
  formatCurrency,
  formatDecimal,
  formatPercent,
} from "../utils/format";

const SHORTCUTS = [
  {
    title: "ROL detalhado",
    description: "Composição da receita operacional líquida e impostos.",
    href: FINANCIAL_ROUTES.rol,
  },
  {
    title: "EBITDA",
    description: "Percentual de EBITDA sobre ROL por filial.",
    href: FINANCIAL_ROUTES.ebitda,
  },
  {
    title: "Custos fixos",
    description: "Peso dos custos fixos sobre a receita.",
    href: FINANCIAL_ROUTES.fixedCost,
  },
  {
    title: "PMR",
    description: "Prazo médio de recebimento em dias.",
    href: FINANCIAL_ROUTES.pmr,
  },
] as const;

const CHART_HEIGHT = 300;

type DashboardFinancialPageProps = {
  pathname?: string;
};

export function DashboardFinancialPage({ pathname }: DashboardFinancialPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useFinancialFilters();

  const { rol, ebitda, fixedCost, pmr, loading, refreshing, requestProgress, error, reload } =
    useFinancialDashboard(apiParams);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = branch ? `Filial ${branch}` : "Consolidado";
  const isBusy = loading || refreshing;
  const hasData =
    rol !== null || ebitda !== null || fixedCost !== null || pmr !== null;

  const comparisonChartData = useMemo(
    () => [
      {
        name: "EBITDA / ROL",
        value: ebitda?.ebitda_over_rol_pct ?? 0,
        key: "ebitda",
      },
      {
        name: "Custos fixos / ROL",
        value: fixedCost?.fixed_cost_over_rol_pct ?? 0,
        key: "fixedCost",
      },
    ],
    [ebitda, fixedCost]
  );

  const hasChartValues = comparisonChartData.some((item) => item.value > 0);

  return (
    <div className="dashboard-financial dashboard-page">
      <FilterBar
        currentPath={pathname ?? FINANCIAL_ROUTES.home}
        filterState={filterState}
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
      <FinancialStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={hasData}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando dashboard financeiro"
      />
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="ROL (com IPI)"
          value={formatCurrency(rol?.rol_with_ipi)}
          subtitle={`${branchLabel} · ${periodLabel}`}
          icon={<TrendingUp size={22} />}
          loading={isBusy && !rol}
        />
        <KpiCard
          title="EBITDA / ROL"
          value={formatPercent(ebitda?.ebitda_over_rol_pct)}
          {...buildKpiGoalPresentation(
            ebitda?.ebitda_value != null
              ? `EBITDA ${formatCurrency(ebitda.ebitda_value)} · ${periodLabel}`
              : periodLabel,
            ebitda,
            formatPercent,
            { realizedValue: ebitda?.ebitda_over_rol_pct },
          )}
          icon={<Percent size={22} />}
          loading={isBusy && !ebitda}
        />
        <KpiCard
          title="Custos fixos / ROL"
          value={formatPercent(fixedCost?.fixed_cost_over_rol_pct)}
          {...buildKpiGoalPresentation(
            fixedCost?.fixed_cost_value != null
              ? `Fixos ${formatCurrency(fixedCost.fixed_cost_value)} · ${periodLabel}`
              : periodLabel,
            fixedCost,
            formatPercent,
            { realizedValue: fixedCost?.fixed_cost_over_rol_pct },
          )}
          icon={<Landmark size={22} />}
          loading={isBusy && !fixedCost}
        />
        <KpiCard
          title="PMR (dias)"
          value={formatDecimal(pmr?.pmr_days, 1)}
          {...buildKpiGoalPresentation(
            periodLabel,
            pmr,
            (v) => formatDecimal(v, 1),
            { realizedValue: pmr?.pmr_days },
          )}
          icon={<Clock size={22} />}
          loading={isBusy && !pmr}
        />
      </section>

      <section className="ds-chart-section">
        <ChartCard
          title="Indicadores percentuais"
          hint={`${branchLabel} · ${periodLabel}`}
        >
        {hasChartValues ? (
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={comparisonChartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
              <YAxis tickFormatter={(v) => `${v}%`} width={48} />
              <Tooltip formatter={(v) => formatPercent(Number(v))} />
              <Bar dataKey="value" radius={[8, 8, 0, 0]} maxBarSize={56}>
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
          <p className="ds-table__empty">Sem dados percentuais para o período.</p>
        )}
        </ChartCard>
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
