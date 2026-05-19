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
import { Percent } from "lucide-react";

import { getEbitdaPct } from "../api/financialApi";
import { ChartCard } from "../components/ChartCard";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { FinancialStatusAlerts } from "../components/FinancialStatusAlerts";
import { CHART_COLORS } from "../constants/chartColors";
import { FINANCIAL_ROUTES } from "../constants/routes";
import { useFinancialFilters } from "../hooks/useFinancialFilters";
import { useFinancialResource } from "../hooks/useFinancialResource";
import type { EbitdaBranchRow } from "../types/financial";
import { formatPeriodLabel } from "../utils/dates";
import { formatCurrency, formatPercent } from "../utils/format";

const CHART_HEIGHT = 320;

type EbitdaPageProps = { pathname?: string };

export function EbitdaPage({ pathname }: EbitdaPageProps) {
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

  const { data, loading, refreshing, error, reload } = useFinancialResource(
    (signal) => getEbitdaPct(apiParams, signal),
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
        value: row.ebitda_over_rol_pct,
      })),
    [branchRows]
  );

  const columns = useMemo<DataTableColumn<EbitdaBranchRow>[]>(
    () => [
      {
        key: "branch",
        header: "Filial",
        render: (row) => row.branch,
      },
      {
        key: "ebitda",
        header: "EBITDA (R$)",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.ebitda_value),
      },
      {
        key: "rol",
        header: "ROL c/ IPI",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.rol_with_ipi),
      },
      {
        key: "pct",
        header: "EBITDA / ROL",
        className: "ds-table__col--numeric",
        render: (row) => formatPercent(row.ebitda_over_rol_pct),
      },
    ],
    []
  );

  const isBusy = loading || refreshing;
  const showBranchChart = !branch && chartData.length > 0;

  return (
    <div className="dashboard-financial dashboard-page">
      <FilterBar
        title="EBITDA"
        subtitle="Percentual de EBITDA sobre ROL"
        currentPath={pathname ?? FINANCIAL_ROUTES.ebitda}
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
        hasData={data !== null}
        onRetry={reload}
      />
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="EBITDA / ROL"
          value={formatPercent(data?.ebitda_over_rol_pct)}
          subtitle={periodLabel}
          icon={<Percent size={22} />}
          loading={isBusy && !data}
        />
        {data?.ebitda_value != null ? (
          <KpiCard
            title="EBITDA"
            value={formatCurrency(data.ebitda_value)}
            subtitle={`ROL ${formatCurrency(data.rol_with_ipi)}`}
            icon={<Percent size={22} />}
            loading={isBusy && !data}
          />
        ) : null}
      </section>

      {showBranchChart ? (
        <section className="ds-charts-grid ds-charts-grid--single">
        <ChartCard title="EBITDA / ROL por filial" hint={periodLabel}>
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
        <section className="ds-table-section">
          <ChartCard title="Por filial" hint={periodLabel}>
            <DataTable
              columns={columns}
              rows={branchRows}
              rowKey={(row) => row.branch}
              loading={isBusy && !data}
            />
          </ChartCard>
        </section>
      ) : null}
    </div>
  );
}
