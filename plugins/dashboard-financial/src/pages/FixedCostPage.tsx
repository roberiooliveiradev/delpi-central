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
import { Landmark } from "lucide-react";

import { getFixedCostPct } from "../api/financialApi";
import { ChartCard } from "../components/ChartCard";
import { DataSourceBanner } from "../components/DataSourceBanner";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { FinancialStatusAlerts } from "../components/FinancialStatusAlerts";
import { CHART_COLORS } from "../constants/chartColors";
import { FINANCIAL_ROUTES } from "../constants/routes";
import { useFinancialFilters } from "../hooks/useFinancialFilters";
import { useFinancialResource } from "../hooks/useFinancialResource";
import type { FixedCostBranchRow } from "../types/financial";
import { formatPeriodLabel } from "../utils/dates";
import {
  buildKpiGoalPresentation,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { formatCurrency, formatPercent } from "../utils/format";
import { FINANCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";

const CHART_HEIGHT = 320;

type FixedCostPageProps = { pathname?: string };

export function FixedCostPage({ pathname }: FixedCostPageProps) {
  const {
    dateStart,
    dateEnd,
    competence,
    branches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    apiParams,
    filterState,
  } = useFinancialFilters();

  const { data, loading, refreshing, requestProgress, error, reload } = useFinancialResource(
    (signal) => getFixedCostPct(apiParams, signal),
    [apiParams.branch, apiParams.end_date, apiParams.start_date]
  );

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const branchRows = data?.branches ?? [];
  const chartData = useMemo(
    () =>
      branchRows.map((row) => ({
        name: formatOperationalUnitCode(row.branch, row.branch),
        value: row.fixed_cost_over_rol_pct,
      })),
    [branchRows]
  );

  const columns = useMemo<DataTableColumn<FixedCostBranchRow>[]>(
    () => [
      { key: "branch", header: OPERATIONAL_UNIT_COLUMN_LABEL, render: (row) => formatOperationalUnitCode(row.branch) },
      {
        key: "fixed",
        header: "Custos fixos (R$)",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.fixed_cost_value),
      },
      {
        key: "rol",
        header: "ROL",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.rol_with_ipi),
      },
      {
        key: "pct",
        header: "Fixos / ROL",
        className: "ds-table__col--numeric",
        render: (row) => formatPercent(row.fixed_cost_over_rol_pct),
      },
    ],
    []
  );

  const isBusy = loading || refreshing;
  const showBranchChart = branches.length === 0 && chartData.length > 0;

  return (
    <div className="dashboard-financial dashboard-page">
      <FilterBar
        title="Custos fixos"
        subtitle="Percentual de custos fixos sobre ROL"
        currentPath={pathname ?? FINANCIAL_ROUTES.fixedCost}
        filterState={filterState}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onRefresh={reload}
        refreshing={refreshing}
      />
      <DataSourceBanner variant="sheets" />
      <FinancialStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={data !== null}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando custos fixos"
      />
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Custos fixos / ROL"
          titleHint={FINANCIAL_HELP_TOOLTIPS.kpis.fixedCostOverRol}
          value={formatDashboardMetricValue(
            data?.fixed_cost_over_rol_pct,
            data,
          )}
          {...buildKpiGoalPresentation(
            periodLabel,
            data,
            undefined,
            { realizedValue: data?.fixed_cost_over_rol_pct },
          )}
          icon={<Landmark size={22} />}
          loading={isBusy && !data}
        />
        {data?.fixed_cost_value != null ? (
          <KpiCard
            title="Custos fixos"
            titleHint={FINANCIAL_HELP_TOOLTIPS.kpis.fixedCostValue}
            value={formatCurrency(data.fixed_cost_value)}
            subtitle={`ROL ${formatCurrency(data.rol_with_ipi)}`}
            icon={<Landmark size={22} />}
            loading={isBusy && !data}
          />
        ) : null}
      </section>

      {showBranchChart ? (
        <section className="ds-charts-grid ds-charts-grid--single">
        <ChartCard title="Custos fixos / ROL por unidade" hint={periodLabel}>
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v) => `${v}%`} width={48} />
              <Tooltip formatter={(v) => formatPercent(Number(v))} />
              <Bar dataKey="value" radius={[8, 8, 0, 0]} maxBarSize={56}>
                {chartData.map((_, index) => (
                  <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        </section>
      ) : null}

      {branchRows.length > 0 ? (
        <DataTableSection
          title="Por unidade"
          hint={periodLabel}
          columns={columns}
          rows={branchRows}
          rowKey={(row) => row.branch}
          loading={loading && branchRows.length === 0}
          refreshing={refreshing}
        />
      ) : null}
    </div>
  );
}