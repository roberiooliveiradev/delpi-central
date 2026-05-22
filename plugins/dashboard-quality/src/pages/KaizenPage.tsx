import { useEffect, useMemo, useState } from "react";
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
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { KaizenFilters } from "../components/KaizenFilters";
import { KpiCard } from "../components/KpiCard";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { CHART_COLORS } from "../constants/chartColors";
import { QUALITY_ROUTES } from "../constants/routes";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useKaizenSummary } from "../hooks/useQualityQueries";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityFilters } from "../hooks/useQualityFilters";
import type { ChartGranularity } from "../types/chart";
import type { Kaizen } from "../types/kaizen";
import {
  aggregateKaizenByStatus,
  aggregateKaizenCountByPeriod,
  aggregateKaizenSavingsBySector,
} from "../utils/chartAggregation";
import { downloadChartSeriesCsv } from "../utils/chartSeriesExport";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import { formatGoalSubtitle } from "../utils/goalDisplay";
import { formatCurrency, formatDecimal } from "../utils/format";
import type { TimeSeriesPoint } from "../utils/timeSeriesAggregation";
import { suggestGranularity } from "../utils/periodBuckets";

const CHART_HEIGHT = 300;

type KaizenPageProps = {
  pathname?: string;
};

function renderPieLabel({
  name,
  percent,
}: {
  name?: string;
  percent?: number;
}) {
  if (!name || percent == null) return "";
  return `${name} ${(percent * 100).toFixed(0)}%`;
}

export function KaizenPage({ pathname }: KaizenPageProps) {
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState("");
  const [granularity, setGranularity] = useState<ChartGranularity>("month");

  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useQualityFilters();

  const debouncedTitle = useDebouncedValue(title);
  const debouncedStatus = useDebouncedValue(status);

  const { branches, loading: branchesLoading } = useQualityBranches(apiParams);

  const summaryParams = useMemo(
    () => ({
      ...apiParams,
      title: debouncedTitle || undefined,
      status: debouncedStatus || undefined,
    }),
    [apiParams, debouncedTitle, debouncedStatus]
  );

  const { data, loading, requestProgress, error, reload } =
    useKaizenSummary(summaryParams);
  const initialLoadingProgress = useLoadingProgress(
    loading && !data,
    requestProgress
  );
  const items = data?.list_kaizen ?? [];

  useEffect(() => {
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  const statusChart = useMemo(() => aggregateKaizenByStatus(items), [items]);
  const sectorChart = useMemo(
    () => aggregateKaizenSavingsBySector(items),
    [items]
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
        header: "Filial",
        render: (row) => row.branch ?? "—",
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
    ],
    []
  );

  const handleExportCsv = () => {
    if (items.length === 0) return;

    downloadCsv(
      "kaizens.csv",
      [
        "Título",
        "Status",
        "Setor",
        "Filial",
        "Implementação",
        "Responsável",
        "Investimento",
        "Economia/dia",
      ],
      items.map((row) => [
        row.title,
        row.status ?? "",
        row.sector ?? "",
        row.branch ?? "",
        formatDisplayDate(row.date_implemented),
        row.accountable ?? "",
        String(row.investment ?? ""),
        String(row.daily_savings ?? ""),
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
        onRefresh={reload}
        refreshing={loading && Boolean(data)}
        actions={
          <button
            type="button"
            className="dq-ghost-btn dq-no-print"
            onClick={handleExportCsv}
            disabled={items.length === 0}
          >
            <Download size={16} />
            Exportar CSV
          </button>
        }
      />

      <div className="dq-no-print">
        <KaizenFilters
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        branches={branches}
        branchesLoading={branchesLoading}
        title={title}
        status={status}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onTitleChange={setTitle}
        onStatusChange={setStatus}
      />
      </div>

      {error ? (
        <div className="dq-state dq-state--error" role="alert">
          <p>{error}</p>
          <button className="dq-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      <section className="dq-kpi-grid" aria-busy={loading}>
        <KpiCard
          title="Total de kaizens"
          value={String(data?.total_kaizens ?? (loading ? "…" : 0))}
          subtitle={formatGoalSubtitle(periodLabel, data, formatDecimal)}
          icon={<Lightbulb size={22} />}
          loading={loading && !data}
        />
        <KpiCard
          title="Economia acumulada"
          value={formatCurrency(data?.total_savings)}
          subtitle="Soma reportada pela API no período"
          icon={<Wallet size={22} />}
          loading={loading && !data}
        />
      </section>

      <section className="dq-chart-section" aria-busy={loading}>
        <ChartCard
          title="Kaizens por período"
          hint="Por data de implementação. Clique em um ponto para filtrar o período."
        >
          <ChartToolbar
            idPrefix="kz-period"
            granularity={granularity}
            onGranularityChange={setGranularity}
            onExportCsv={handleExportPeriodCsv}
            exportDisabled={periodChart.length === 0}
          />

          {periodChart.length === 0 && !loading ? (
            <div className="dq-state-box">Sem dados para o gráfico.</div>
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
        <ChartCard title="Kaizens por status">
          {statusChart.length === 0 && !loading ? (
            <div className="dq-state-box">Sem dados para o gráfico.</div>
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

        <ChartCard title="Economia por setor (top 8)">
          {sectorChart.length === 0 && !loading ? (
            <div className="dq-state-box">Sem dados para o gráfico.</div>
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
                  formatter={(value) => [formatDecimal(Number(value)), "Economia/dia"]}
                />
                <Bar dataKey="value" fill={CHART_COLORS[0]} radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      {loading && !data ? (
        <LoadingActivityCard
          title="Carregando kaizens"
          description="Buscando melhorias cadastradas para o período."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <DataTableSection
        title="Lista de kaizens"
        columns={columns}
        rows={items}
        rowKey={(row) => row.id}
        loading={loading && !data}
        emptyMessage="Nenhum kaizen encontrado para os filtros."
        searchPlaceholder="Buscar título, setor, status…"
        getSearchText={(row) =>
          [row.title, row.sector, row.status, row.branch].filter(Boolean).join(" ")
        }
      />
    </div>
  );
}
