import { GHOST_BTN } from "../ui/ghostChrome";
import { useCallback, useMemo, useState } from "react";
import { useChartGranularitySelection } from "@delpi/plugin-ui/index";
import { Download, Lightbulb, Wallet } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { KaizenFilters } from "../components/KaizenFilters";
import { QualityStatusAlerts } from "../components/QualityStatusAlerts";
import { KpiCard } from "../components/KpiCard";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { CHART_COLORS } from "../constants/chartColors";
import { buildKaizenDetailPath, QUALITY_ROUTES } from "../constants/routes";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useKaizenSummary } from "../hooks/useQualityQueries";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityFilters } from "../hooks/useQualityFilters";
import type { Kaizen } from "../types/kaizen";
import {
  aggregateKaizenByStatus,
  aggregateKaizenCountByPeriod,
  aggregateKaizenSavingsBySector,
} from "../utils/chartAggregation";
import { downloadChartSeriesCsv } from "../utils/chartSeriesExport";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import {
  buildKpiGoalPresentation,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { formatCurrency, formatDecimal } from "../utils/format";
import { navigateQuality } from "../utils/navigation";
import type { TimeSeriesPoint } from "../utils/timeSeriesAggregation";
import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";
import { STATE_BOX_EMPTY } from "../ui/stateChrome";

const CHART_HEIGHT = 300;

type KaizenPageProps = {
  pathname?: string;
};

function renderPieLabel({
  name,
  percent,
  value,
}: {
  name?: string;
  percent?: number;
  value?: number;
}) {
  if (!name || percent == null) return "";
  const count =
    typeof value === "number" && Number.isFinite(value) ? ` (${Math.round(value)})` : "";
  return `${name}${count} ${(percent * 100).toFixed(0)}%`;
}

export function KaizenPage({ pathname }: KaizenPageProps) {
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState("");

  const {
    dateStart,
    dateEnd,
    competence,
    branches: selectedBranches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    apiParams,
    filterState,
  } = useQualityFilters();

  const { granularity, setGranularity } = useChartGranularitySelection(
    dateStart,
    dateEnd,
  );

  const debouncedTitle = useDebouncedValue(title);
  const debouncedStatus = useDebouncedValue(status);

  const { branches: branchOptions, loading: branchesLoading } = useQualityBranches(apiParams);

  const summaryParams = useMemo(
    () => ({
      ...apiParams,
      title: debouncedTitle || undefined,
      status: debouncedStatus || undefined,
    }),
    [apiParams, debouncedTitle, debouncedStatus]
  );

  const listParams = useMemo(
    () => ({
      branch: apiParams.branch,
      title: debouncedTitle || undefined,
      status: debouncedStatus || undefined,
    }),
    [apiParams.branch, debouncedTitle, debouncedStatus]
  );

  const { data, loading, requestProgress, error, reload } =
    useKaizenSummary(summaryParams);
  const {
    data: listData,
    loading: listLoading,
    error: listError,
    reload: reloadList,
  } = useKaizenSummary(listParams);
  const isRefreshing = loading && Boolean(data);
  const items = data?.list_kaizen ?? [];
  const savingsItems = data?.list_savings_kaizen ?? [];
  const listItems = listData?.list_kaizen ?? [];

  const statusChart = useMemo(() => aggregateKaizenByStatus(items), [items]);
  const sectorChart = useMemo(
    () => aggregateKaizenSavingsBySector(savingsItems),
    [savingsItems]
  );
  const periodChart = useMemo(
    () =>
      aggregateKaizenCountByPeriod(items, dateStart, dateEnd, granularity),
    [items, dateStart, dateEnd, granularity]
  );

  const periodLabel = formatPeriodLabel(dateStart, dateEnd);

  const columns = useMemo<DataTableColumn<Kaizen>[]>(
    () => [
      {
        key: "title",
        header: "Título",
        className: "dq-table__col--wide",
        render: (row) => row.title,
      },
      {
        key: "status",
        header: "Status",
        render: (row) => row.status ?? "—",
      },
      {
        key: "sector",
        header: "Setor",
        render: (row) => row.sector ?? "—",
      },
      {
        key: "branch",
        header: OPERATIONAL_UNIT_COLUMN_LABEL,
        render: (row) => formatOperationalUnitCode(row.branch),
      },
      {
        key: "date_implemented",
        header: "Implementação",
        render: (row) => formatDisplayDate(row.date_implemented),
      },
      {
        key: "accountable",
        header: "Responsável",
        render: (row) => row.accountable ?? "—",
      },
      {
        key: "investment",
        header: "Investimento",
        className: "dq-table__col--numeric",
        render: (row) => formatCurrency(row.investment),
      },
      {
        key: "daily_savings",
        header: "Economia/dia",
        className: "dq-table__col--numeric",
        render: (row) => formatCurrency(row.daily_savings),
      },
      {
        key: "annual_savings",
        header: "Economia/ano",
        className: "dq-table__col--numeric",
        render: (row) => formatCurrency(row.annual_savings),
      },
    ],
    []
  );

  const handleKaizenRowClick = useCallback((row: Kaizen) => {
    if (!row.id) return;
    navigateQuality(buildKaizenDetailPath(row.id), filterState);
  }, []);

  const handleReload = useCallback(() => {
    reload();
    reloadList();
  }, [reload, reloadList]);

  const handleExportCsv = () => {
    if (listItems.length === 0) return;

    downloadCsv(
      "kaizens.csv",
      [
        "Título",
        "Status",
        "Setor",
        "Unidade",
        "Implementação",
        "Responsável",
        "Investimento",
        "Economia/dia",
        "Economia/ano",
      ],
      listItems.map((row) => [
        row.title,
        row.status ?? "",
        row.sector ?? "",
        formatOperationalUnitCode(row.branch, ""),
        formatDisplayDate(row.date_implemented),
        row.accountable ?? "",
        String(row.investment ?? ""),
        String(row.daily_savings ?? ""),
        String(row.annual_savings ?? ""),
      ])
    );
  };

  const handleChartDrillDown = (point: TimeSeriesPoint) => {
    if (!point.dateStart || !point.dateEnd) return;
    setDateStart(point.dateStart);
    setDateEnd(point.dateEnd);
  };

  const handleExportPeriodCsv = () => {
    downloadChartSeriesCsv(
      "kaizens-por-periodo.csv",
      periodChart.map((point) => ({
        periodo: point.periodo,
        value: point.value,
        valueLabel: "Quantidade",
      }))
    );
  };

  return (
    <div className="dashboard-quality dashboard-page dq-print-root">
      <QualityPageHeader
        title="Kaizens"
        subtitle="Melhorias implementadas e economia gerada"
        currentPath={pathname ?? QUALITY_ROUTES.kaizen}
        filterState={filterState}
        printDisabled={loading && !data}
        onRefresh={handleReload}
        refreshing={loading && Boolean(data)}
        actions={
          <button
            type="button"
            className={`${GHOST_BTN} dq-no-print`}
            onClick={handleExportCsv}
            disabled={listItems.length === 0}
          >
            <Download size={16} />
            Exportar CSV
          </button>
        }
      />

      <div className="dq-no-print">
        <KaizenFilters
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        selectedBranches={selectedBranches}
        branchOptions={branchOptions}
        branchesLoading={branchesLoading}
        title={title}
        status={status}
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onTitleChange={setTitle}
        onStatusChange={setStatus}
      />
      </div>

      <QualityStatusAlerts
        error={error ?? listError}
        loading={loading || listLoading}
        refreshing={isRefreshing}
        hasData={Boolean(data)}
        requestProgress={requestProgress}
        onRetry={handleReload}
        refreshTitle="Atualizando kaizens"
        initialTitle="Carregando kaizens"
        initialDescription="Buscando melhorias cadastradas para o período."
      />

      <section className="dq-kpi-grid" aria-busy={loading}>
        <KpiCard
          title="Ideias aprovadas para Kaizen/mês"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.kaizenIdeas}
          value={formatDashboardMetricValue(data?.total_kaizens, data?.ideas_goal ?? data)}
          {...buildKpiGoalPresentation(
            periodLabel,
            data?.ideas_goal ?? data,
            undefined,
            { realizedValue: data?.total_kaizens },
          )}
          icon={<Lightbulb size={22} />}
          loading={loading && !data}
        />
        <KpiCard
          title="Ganhos financeiros do kaizen"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.kaizenFinancialGains}
          value={formatDashboardMetricValue(data?.total_savings, data)}
          {...buildKpiGoalPresentation(
            periodLabel,
            data,
            undefined,
            { realizedValue: data?.total_savings },
          )}
          icon={<Wallet size={22} />}
          loading={loading && !data}
        />
      </section>

      <section className="dq-chart-section" aria-busy={loading}>
        <ChartCard
          title="Kaizens por período"
          hint={`${QUALITY_HELP_TOOLTIPS.charts.kaizenByPeriod} Clique em um ponto para filtrar o período.`}
        >
          <ChartToolbar
            idPrefix="kz-period"
            granularity={granularity}
            onGranularityChange={setGranularity}
            onExportCsv={handleExportPeriodCsv}
            exportDisabled={periodChart.length === 0}
          />

          {periodChart.length === 0 && !loading ? (
            <div className={STATE_BOX_EMPTY}>Sem dados para o gráfico.</div>
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <LineChart
                data={periodChart}
                onClick={(state) => {
                  const rawIndex = state?.activeTooltipIndex;
                  const index =
                    typeof rawIndex === "number" ? rawIndex : Number(rawIndex);
                  if (!Number.isFinite(index) || index < 0) return;
                  const point = periodChart[index];
                  if (point) handleChartDrillDown(point);
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="periodo"
                  tick={{ fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => [
                    formatDecimal(Number(value)),
                    "Kaizens",
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={CHART_COLORS[2]}
                  strokeWidth={2}
                  dot={{ r: 4, cursor: "pointer" }}
                  activeDot={{ r: 6, cursor: "pointer" }}
                  name="Kaizens"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      <section className="dq-charts-grid" aria-busy={loading}>
        <ChartCard
          title="Kaizens por status"
          hint={QUALITY_HELP_TOOLTIPS.charts.kaizenByStatus}
        >
          {statusChart.length === 0 && !loading ? (
            <div className={STATE_BOX_EMPTY}>Sem dados para o gráfico.</div>
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <PieChart>
                <Pie
                  data={statusChart}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={renderPieLabel}
                >
                  {statusChart.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard
          title="Economia por setor (top 8)"
          hint={QUALITY_HELP_TOOLTIPS.charts.kaizenSavingsBySector}
        >
          {sectorChart.length === 0 && !loading ? (
            <div className={STATE_BOX_EMPTY}>Sem dados para o gráfico.</div>
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={sectorChart} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={120}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip
                  formatter={(value) => [
                    formatCurrency(Number(value)),
                    "Ganho no período",
                  ]}
                />
                <Bar dataKey="value" fill={CHART_COLORS[0]} radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      <DataTableSection
        columnPreferencesKey="dashboard-quality:KaizenPage:lista-de-kaizens:v1"
        title="Lista de kaizens"
        hint="Todos os kaizens implantados, independente do período filtrado."
        columns={columns}
        rows={listItems}
        rowKey={(row) => row.id}
        loading={listLoading && !listData}
        emptyMessage="Nenhum kaizen encontrado para os filtros."
        searchPlaceholder="Buscar título, setor, status…"
        getSearchText={(row) =>
          [row.title, row.sector, row.status, row.branch].filter(Boolean).join(" ")
        }
        onRowClick={handleKaizenRowClick}
      />
    </div>
  );
}