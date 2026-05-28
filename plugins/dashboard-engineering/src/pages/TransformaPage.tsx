import { useEffect, useMemo, useState } from "react";
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
import { Clock, Coins, Lightbulb, Percent } from "lucide-react";

import { getTransformaProcesses, getTransformaSummary } from "../api/engineeringApi";
import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import { DataSourceBanner } from "../components/DataSourceBanner";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { EngineeringStatusAlerts } from "../components/EngineeringStatusAlerts";
import { CHART_COLORS } from "../constants/chartColors";
import { ENGINEERING_ROUTES } from "../constants/routes";
import { useEngineeringFilters } from "../hooks/useEngineeringFilters";
import { useEngineeringResource } from "../hooks/useEngineeringResource";
import type { ChartGranularity } from "../types/chart";
import type { TransformaProcess } from "../types/engineering";
import { buildTransformaSavingsSeries } from "../utils/chartMonthlySeries";
import { formatPeriodLabel } from "../utils/dates";
import { buildKpiGoalPresentation } from "../utils/goalDisplay";
import { suggestGranularity } from "../utils/periodBuckets";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
  formatPercent,
} from "../utils/format";

const LINE_CHART_HEIGHT = 320;
const TOP_BAR_ROW_HEIGHT = 40;

type TransformaPageProps = { pathname?: string };

export function TransformaPage({ pathname }: TransformaPageProps) {
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

  const [statusFilter, setStatusFilter] = useState("");
  const [granularity, setGranularity] = useState<ChartGranularity>("month");

  const listParams = useMemo(
    () => ({
      ...apiParams,
      status: statusFilter || undefined,
    }),
    [apiParams, statusFilter]
  );

  const {
    data: summary,
    loading: summaryLoading,
    refreshing: summaryRefreshing,
    requestProgress: summaryRequestProgress,
    error: summaryError,
    reload: reloadSummary,
  } = useEngineeringResource(
    (signal) => getTransformaSummary(apiParams, signal),
    [apiParams.branch, apiParams.end_date, apiParams.filial_id, apiParams.start_date]
  );

  const {
    data: processesData,
    loading: listLoading,
    refreshing: listRefreshing,
    requestProgress: listRequestProgress,
    error: listError,
    reload: reloadList,
  } = useEngineeringResource(
    (signal) => getTransformaProcesses(listParams, signal),
    [
      listParams.branch,
      listParams.end_date,
      listParams.filial_id,
      listParams.start_date,
      listParams.status,
    ]
  );

  const reload = () => {
    reloadSummary();
    reloadList();
  };

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const items = processesData?.items ?? [];
  const loading = summaryLoading || listLoading;
  const refreshing = summaryRefreshing || listRefreshing;
  const requestProgress = useMemo(
    () => ({
      completed:
        summaryRequestProgress.completed + listRequestProgress.completed,
      total: summaryRequestProgress.total + listRequestProgress.total,
    }),
    [
      summaryRequestProgress.completed,
      summaryRequestProgress.total,
      listRequestProgress.completed,
      listRequestProgress.total,
    ]
  );
  const error = summaryError && listError ? summaryError : null;
  const isBusy = loading || refreshing;
  const hasData = summary !== null || processesData !== null;

  useEffect(() => {
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  const savingsChartData = useMemo(
    () =>
      buildTransformaSavingsSeries(
        items,
        summary?.monthly_breakdown ?? [],
        dateStart,
        dateEnd,
        granularity
      ),
    [items, summary?.monthly_breakdown, dateStart, dateEnd, granularity]
  );

  const topSavingsChart = useMemo(
    () =>
      [...items]
        .filter((item) => (item.daily_savings ?? 0) > 0)
        .sort((a, b) => (b.daily_savings ?? 0) - (a.daily_savings ?? 0))
        .slice(0, 10)
        .map((item) => ({
          name:
            item.name_process.length > 28
              ? `${item.name_process.slice(0, 28)}…`
              : item.name_process,
          value: item.daily_savings ?? 0,
        })),
    [items]
  );

  const topSavingsChartHeight = useMemo(
    () => Math.max(280, topSavingsChart.length * TOP_BAR_ROW_HEIGHT + 48),
    [topSavingsChart.length]
  );

  const columns = useMemo<DataTableColumn<TransformaProcess>[]>(
    () => [
      {
        key: "name",
        header: "Processo",
        className: "ds-table__col--wide",
        render: (row) => row.name_process || "—",
      },
      { key: "filial", header: "Filial", render: (row) => row.filial_id ?? "—" },
      { key: "sector", header: "Setor", render: (row) => row.sector_name ?? "—" },
      { key: "status", header: "Status", render: (row) => row.status ?? "—" },
      {
        key: "daily",
        header: "Economia/dia",
        className: "ds-table__col--numeric",
        render: (row) => formatCurrency(row.daily_savings),
      },
      {
        key: "payback",
        header: "Payback (meses)",
        className: "ds-table__col--numeric",
        render: (row) => formatDecimal(row.payback_months, 1),
      },
      {
        key: "impl",
        header: "Implantação",
        render: (row) => row.implementetion_date ?? "—",
      },
    ],
    []
  );

  return (
    <div className="dashboard-engineering dashboard-page">
      <FilterBar
        title="TRANSFORMA+ DELPI"
        subtitle="Ganhos financeiros e processos de melhoria (Postgres transformometro)"
        currentPath={pathname ?? ENGINEERING_ROUTES.transforma}
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
      <DataSourceBanner variant="transforma" />
      <p className="ds-hint" style={{ margin: "0 0 1rem" }}>
        Dados via API de engenharia, lidos do schema{" "}
        <strong>transformometro</strong>. Cadastro completo no app{" "}
        <a href="/apps/transformometro/dashboard">Transformômetro</a>.
      </p>
      <EngineeringStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={hasData}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando TRANSFORMA+"
      />

      <section className="ds-filters-row">
        <div className="ds-filter-box">
          <label htmlFor="de-transforma-status">Status do processo</label>
          <input
            id="de-transforma-status"
            type="text"
            value={statusFilter}
            placeholder="Todos"
            onChange={(e) => setStatusFilter(e.target.value)}
          />
        </div>
      </section>

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Ganhos brutos no período"
          value={formatCurrency(summary?.total_gross_savings_in_period)}
          {...buildKpiGoalPresentation(
            periodLabel,
            summary,
            undefined,
            { realizedValue: summary?.total_gross_savings_in_period },
          )}
          icon={<Coins size={22} />}
          loading={isBusy && !summary}
        />
        <KpiCard
          title="Economia líquida"
          value={formatCurrency(summary?.total_net_savings_until_now)}
          contextLabel="Acumulado no recorte"
          icon={<Coins size={22} />}
          loading={isBusy && !summary}
        />
        <KpiCard
          title="Soluções implementadas"
          value={formatInteger(summary?.implemented_solutions_count)}
          contextLabel="Cenários de melhoria"
          icon={<Lightbulb size={22} />}
          loading={isBusy && !summary}
        />
        <KpiCard
          title="Horas economizadas"
          value={formatDecimal(summary?.total_hours_saved_until_now, 1)}
          contextLabel={periodLabel}
          icon={<Clock size={22} />}
          loading={isBusy && !summary}
        />
        <KpiCard
          title="ROI médio"
          value={formatPercent(summary?.average_roi, 1)}
          {...buildKpiGoalPresentation(
            "Média no período",
            summary,
            (v) => formatPercent(v, 1),
            {
              realizedValue: summary?.average_roi,
              showGoal: false,
            },
          )}
          icon={<Percent size={22} />}
          loading={isBusy && !summary}
        />
        <KpiCard
          title="Processos listados"
          value={String(processesData?.total ?? items.length)}
          contextLabel="Com filtros aplicados"
          icon={<Lightbulb size={22} />}
          loading={isBusy && !processesData}
        />
      </section>

      <section className="ds-chart-section">
        <ChartCard title="Economia líquida no período" hint={periodLabel}>
          <ChartToolbar
            idPrefix="transforma-savings"
            granularity={granularity}
            onGranularityChange={setGranularity}
          />
          {savingsChartData.length === 0 && !isBusy ? (
            <p className="ds-state-box">
              Sem economia líquida no período para o agrupamento selecionado.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={LINE_CHART_HEIGHT}>
              <LineChart data={savingsChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis
                  tickFormatter={(v) => formatCurrency(Number(v))}
                  width={88}
                  domain={[
                    0,
                    (dataMax: number) =>
                      dataMax > 0 ? Math.ceil(dataMax * 1.15) : 1,
                  ]}
                />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Line
                  type="monotone"
                  dataKey="net"
                  stroke={CHART_COLORS[0]}
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      {topSavingsChart.length > 0 ? (
        <section className="ds-chart-section ds-chart-section--tall">
          <ChartCard title="Top economia diária" hint="10 maiores no filtro">
            <ResponsiveContainer width="100%" height={topSavingsChartHeight}>
              <BarChart
                data={topSavingsChart}
                layout="vertical"
                margin={{ left: 4, right: 16, top: 8, bottom: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v) => formatCurrency(Number(v))} />
                <YAxis type="category" dataKey="name" width={168} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} maxBarSize={32}>
                  {topSavingsChart.map((_, index) => (
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

      <DataTableSection
        title="Lista de processos"
        hint={periodLabel}
        columns={columns}
        rows={items}
        rowKey={(row) => row.id}
        loading={listLoading && items.length === 0}
        refreshing={listRefreshing}
        emptyMessage="Nenhum processo encontrado para os filtros."
        searchPlaceholder="Buscar processo, setor, status…"
        getSearchText={(row) =>
          [
            row.name_process,
            row.filial_id,
            row.sector_name,
            row.status,
          ]
            .filter(Boolean)
            .join(" ")
        }
      />
    </div>
  );
}
