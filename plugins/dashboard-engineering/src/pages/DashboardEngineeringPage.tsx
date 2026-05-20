import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Clock, Coins, Lightbulb, Percent, Wrench } from "lucide-react";

import { ChartCard } from "../components/ChartCard";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { ModuleShortcut } from "../components/ModuleShortcut";
import { EngineeringStatusAlerts } from "../components/EngineeringStatusAlerts";
import { CHART_COLORS } from "../constants/chartColors";
import { ENGINEERING_ROUTES, LMP_DASHBOARD_PATH } from "../constants/routes";
import { useEngineeringDashboard } from "../hooks/useEngineeringDashboard";
import { useEngineeringFilters } from "../hooks/useEngineeringFilters";
import { formatPeriodLabel, monthKeyToLabel } from "../utils/dates";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
  formatPercent,
} from "../utils/format";

const CHART_HEIGHT = 300;

const SHORTCUTS = [
  {
    title: "Processos Transforma+",
    description: "Lista de processos, economia diária, payback e status.",
    href: ENGINEERING_ROUTES.processes,
    external: false,
  },
  {
    title: "Dashboard LMPs",
    description: "% de projetos/LMPs no prazo — painel operacional separado.",
    href: LMP_DASHBOARD_PATH,
    external: true,
  },
] as const;

type DashboardEngineeringPageProps = {
  pathname?: string;
};

export function DashboardEngineeringPage({ pathname }: DashboardEngineeringPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useEngineeringFilters();

  const { summary, loading, refreshing, error, reload } =
    useEngineeringDashboard(apiParams);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = branch ? `Filial ${branch}` : "Todas as filiais";
  const isBusy = loading || refreshing;
  const hasData = summary !== null;

  const savingsChartData = useMemo(
    () =>
      (summary?.monthly_breakdown ?? []).map((item) => ({
        name: monthKeyToLabel(item.month),
        gross: item.gross_savings_month,
        net: item.net_savings_month,
      })),
    [summary?.monthly_breakdown]
  );

  const hasChartValues = savingsChartData.some(
    (item) => item.gross > 0 || item.net > 0
  );

  return (
    <div className="dashboard-engineering dashboard-page">
      <FilterBar
        currentPath={pathname ?? ENGINEERING_ROUTES.home}
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
      <EngineeringStatusAlerts
        error={error}
        loading={loading}
        hasData={hasData}
        onRetry={reload}
      />
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Ganhos brutos no período"
          value={formatCurrency(summary?.total_gross_savings_in_period)}
          subtitle={`${branchLabel} · ${periodLabel}`}
          icon={<Coins size={22} />}
          loading={isBusy && !summary}
        />
        <KpiCard
          title="Economia líquida acumulada"
          value={formatCurrency(summary?.total_net_savings_until_now)}
          subtitle="No recorte filtrado"
          icon={<Coins size={22} />}
          loading={isBusy && !summary}
        />
        <KpiCard
          title="Soluções implementadas"
          value={formatInteger(summary?.implemented_solutions_count)}
          subtitle="Processos com cenário de melhoria"
          icon={<Lightbulb size={22} />}
          loading={isBusy && !summary}
        />
        <KpiCard
          title="Horas economizadas"
          value={formatDecimal(summary?.total_hours_saved_until_now, 1)}
          subtitle={periodLabel}
          icon={<Clock size={22} />}
          loading={isBusy && !summary}
        />
        <KpiCard
          title="ROI médio"
          value={formatPercent(summary?.average_roi, 1)}
          subtitle="Média dos processos no período"
          icon={<Percent size={22} />}
          loading={isBusy && !summary}
        />
      </section>

      <section className="ds-chart-section">
        <ChartCard
          title="Ganhos mensais (Transforma+)"
          hint={`${branchLabel} · ${periodLabel}`}
        >
          {hasChartValues ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <LineChart data={savingsChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => formatCurrency(Number(v))} width={72} />
                <Tooltip
                  formatter={(v, name) => [
                    formatCurrency(Number(v)),
                    name === "gross" ? "Bruto" : "Líquido",
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="gross"
                  name="gross"
                  stroke={CHART_COLORS[0]}
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="net"
                  name="net"
                  stroke={CHART_COLORS[1]}
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="ds-table__empty">Sem ganhos mensais no período.</p>
          )}
        </ChartCard>
      </section>

      {savingsChartData.length > 0 ? (
        <section className="ds-charts-grid ds-charts-grid--single">
          <ChartCard title="Economia líquida por mês" hint={periodLabel}>
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={savingsChartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => formatCurrency(Number(v))} width={72} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="net" radius={[8, 8, 0, 0]} maxBarSize={56}>
                  {savingsChartData.map((_, index) => (
                    <Cell
                      key={index}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </section>
      ) : null}

      <section className="ds-shortcuts-grid">
        {SHORTCUTS.map((item) => (
          <ModuleShortcut
            key={item.href}
            title={item.title}
            description={item.description}
            href={item.href}
            filterState={item.external ? undefined : filterState}
            external={item.external}
          />
        ))}
      </section>

      <p className="ds-page-subtitle" style={{ marginTop: "1rem" }}>
        <Wrench size={14} style={{ verticalAlign: "middle", marginRight: 6 }} />
        Indicador estratégico <strong>% projetos no prazo</strong> (LMP) permanece no{" "}
        <a href={LMP_DASHBOARD_PATH}>Dashboard LMPs</a>.
      </p>
    </div>
  );
}
