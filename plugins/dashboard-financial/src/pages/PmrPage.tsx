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
import { Clock } from "lucide-react";

import { getPmr } from "../api/financialApi";
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
import type { PmrBranchRow } from "../types/financial";
import { formatPeriodLabel } from "../utils/dates";
import {
  buildKpiGoalPresentation,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { formatDecimal } from "../utils/format";
import { FINANCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";

const CHART_HEIGHT = 320;

type PmrPageProps = { pathname?: string };

export function PmrPage({ pathname }: PmrPageProps) {
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

  const { data, loading, refreshing, requestProgress, error, reload } = useFinancialResource(
    (signal) => getPmr(apiParams, signal),
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
        name: `Filial ${row.branch}`,
        value: row.pmr_days,
      })),
    [branchRows]
  );

  const columns = useMemo<DataTableColumn<PmrBranchRow>[]>(
    () => [
      { key: "branch", header: "Filial", render: (row) => row.branch },
      {
        key: "pmr",
        header: "PMR (dias)",
        className: "ds-table__col--numeric",
        render: (row) => formatDecimal(row.pmr_days, 1),
      },
    ],
    []
  );

  const isBusy = loading || refreshing;
  const showBranchChart = !branch && chartData.length > 0;

  return (
    <div className="dashboard-financial dashboard-page">
      <FilterBar
        title="PMR"
        subtitle="Prazo médio de recebimento"
        currentPath={pathname ?? FINANCIAL_ROUTES.pmr}
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
      <DataSourceBanner variant="sheets" />
      <FinancialStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={data !== null}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando PMR"
      />
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="PMR (dias)"
          titleHint={FINANCIAL_HELP_TOOLTIPS.kpis.pmr}
          value={formatDashboardMetricValue(data?.pmr_days, data)}
          {...buildKpiGoalPresentation(
            periodLabel,
            data,
            undefined,
            { realizedValue: data?.pmr_days },
          )}
          icon={<Clock size={22} />}
          loading={isBusy && !data}
        />
      </section>

      {showBranchChart ? (
        <section className="ds-charts-grid ds-charts-grid--single">
        <ChartCard title="PMR por filial" hint={periodLabel}>
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis width={48} />
              <Tooltip formatter={(v) => `${formatDecimal(Number(v), 1)} dias`} />
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
          title="Por filial"
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