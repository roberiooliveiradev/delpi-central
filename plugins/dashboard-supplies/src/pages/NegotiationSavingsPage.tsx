import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { HandCoins, TrendingUp } from "lucide-react";

import { getNegotiationSavings } from "../api/suppliesApi";
import { ChartCard } from "../components/ChartCard";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { FilterBar } from "../components/FilterBar";
import { InfoCard } from "../components/InfoCard";
import { KpiCard } from "../components/KpiCard";
import { SuppliesStatusAlerts } from "../components/SuppliesStatusAlerts";
import { CHART_COLORS } from "../constants/chartColors";
import { SUPPLIES_ROUTES } from "../constants/routes";
import { useSuppliesFilters } from "../hooks/useSuppliesFilters";
import { useSuppliesResource } from "../hooks/useSuppliesResource";
import type {
  NegotiationSavingsBranchItem,
  NegotiationSavingsEntry,
} from "../types/supplies";
import { buildNegotiationSavingsTrendSeries } from "../utils/chartMonthlySeries";
import { formatPeriodLabel, formatDisplayDate } from "../utils/dates";
import { buildKpiGoalPresentation, formatDashboardMetricValue } from "../utils/goalDisplay";
import { formatBranchFilterLabel } from "../utils/branchClientFilters";
import { formatChartCurrency, formatCurrency, formatInteger } from "../utils/format";
import { SUPPLIES_HELP_TOOLTIPS } from "../content/helpTooltips";

const CHART_HEIGHT = 320;

type NegotiationSavingsPageProps = { pathname?: string };

export function NegotiationSavingsPage({ pathname }: NegotiationSavingsPageProps) {
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
    (signal) =>
      getNegotiationSavings(
        {
          start_date: periodParams.start_date,
          end_date: periodParams.end_date,
          branch: periodParams.branch,
        },
        signal
      ),
    [periodParams.branch, periodParams.end_date, periodParams.start_date]
  );

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = formatBranchFilterLabel(branches);
  const isBusy = loading || refreshing;

  const monthlyChart = useMemo(
    () => buildNegotiationSavingsTrendSeries(data?.entries ?? [], dateStart, dateEnd),
    [data?.entries, dateStart, dateEnd]
  );

  const branchChart = useMemo(
    () =>
      (data?.branches ?? []).map((item) => ({
        name: `Filial ${item.branch ?? "—"}`,
        value: Number(item.total_savings ?? 0),
      })),
    [data?.branches]
  );

  const branchColumns = useMemo<DataTableColumn<NegotiationSavingsBranchItem>[]>(
    () => [
      {
        key: "branch",
        header: "Filial",
        render: (row) => (row.branch ? `Filial ${row.branch}` : "—"),
      },
      {
        key: "total",
        header: "Economia no período",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.total_savings),
      },
    ],
    []
  );

  const entryColumns = useMemo<DataTableColumn<NegotiationSavingsEntry>[]>(
    () => [
      {
        key: "date",
        header: "Data",
        render: (row) => formatDisplayDate(row.date),
      },
      {
        key: "branch",
        header: "Filial",
        render: (row) => (row.branch ? `Filial ${row.branch}` : "—"),
      },
      {
        key: "amount",
        header: "Economia",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.savings_amount),
      },
    ],
    []
  );

  const realizedValue =
    data?.summary.total_savings ?? data?.total_savings ?? null;

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        title="Economia em negociações de compras"
        subtitle="Valores registrados na planilha IDD Suprimentos (Google Sheets)"
        currentPath={pathname ?? SUPPLIES_ROUTES.negotiationSavings}
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
        showLocationFilter={false}
      />
      <div className="ds-source-banners" role="note">
        <InfoCard variant="info" icon={<HandCoins size={18} />} title="Google Sheets — IDD Suprimentos">
          Economia em reais por filial e data de registro. Metas alinhadas ao indicador
          estratégico <em>supplies-negotiation-savings</em>.
        </InfoCard>
      </div>
      <SuppliesStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={data !== null}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando economia em negociações"
      />

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Economia total"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.savingsTotal}
          value={formatDashboardMetricValue(realizedValue, data?.summary)}
          {...buildKpiGoalPresentation(
            `${branchLabel} · ${periodLabel}`,
            data?.summary,
            undefined,
            { realizedValue },
          )}
          icon={<HandCoins size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Lançamentos no período"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.savingsEntries}
          value={formatInteger(data?.entries.length)}
          subtitle="Registros na planilha IDD"
          icon={<TrendingUp size={22} />}
          loading={isBusy && !data}
        />
      </section>

      <section className="ds-charts-grid">
        <ChartCard
          title="Economia no período"
          titleHint={SUPPLIES_HELP_TOOLTIPS.kpis.savingsPeriod}
          hint="Soma mensal dos lançamentos da planilha."
        >
          {monthlyChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <LineChart data={monthlyChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis tickFormatter={(value) => formatChartCurrency(value)} />
                <Tooltip formatter={(value) => formatChartCurrency(Number(value))} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="savings"
                  name="Economia"
                  stroke={CHART_COLORS[0]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Sem lançamentos no período.</div>
          )}
        </ChartCard>

        <ChartCard title="Economia por filial">
          {branchChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={branchChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis tickFormatter={(value) => formatChartCurrency(value)} />
                <Tooltip formatter={(value) => formatChartCurrency(Number(value))} />
                <Bar dataKey="value" name="Economia" radius={[8, 8, 0, 0]} maxBarSize={48}>
                  {branchChart.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Sem dados por filial.</div>
          )}
        </ChartCard>
      </section>

      <DataTableSection
        title="Totais por filial"
        columns={branchColumns}
        rows={data?.branches ?? []}
        rowKey={(row) => row.branch ?? "branch"}
        loading={loading && !(data?.branches?.length)}
        refreshing={refreshing}
        emptyMessage="Nenhum total por filial no período."
      />

      <DataTableSection
        title="Lançamentos da planilha"
        hint="Cada linha corresponde a um registro de economia em negociação."
        columns={entryColumns}
        rows={data?.entries ?? []}
        rowKey={(row) => `${row.branch}-${row.date}-${row.savings_amount}`}
        loading={loading && !(data?.entries?.length)}
        refreshing={refreshing}
        emptyMessage="Nenhum lançamento no período."
        searchPlaceholder="Buscar filial ou data…"
      />
    </div>
  );
}