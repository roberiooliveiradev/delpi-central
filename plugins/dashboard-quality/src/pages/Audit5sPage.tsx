import { GHOST_BTN } from "../ui/ghostChrome";
import { useMemo } from "react";
import { useChartGranularitySelection } from "@delpi/plugin-ui/index";
import { ClipboardCheck, Download, Star } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Audit5sFilters } from "../components/Audit5sFilters";
import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { KpiCard } from "../components/KpiCard";
import { QualityStatusAlerts } from "../components/QualityStatusAlerts";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { CHART_COLORS } from "../constants/chartColors";
import { QUALITY_ROUTES } from "../constants/routes";
import { useAudit5sSummary } from "../hooks/useQualityQueries";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityFilters } from "../hooks/useQualityFilters";
import type { Audit5s } from "../types/audit5s";
import {
  aggregateAudit5sByArea,
  aggregateAudit5sScoreByPeriod,
} from "../utils/chartAggregation";
import { downloadChartSeriesCsv } from "../utils/chartSeriesExport";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import {
  buildKpiGoalPresentation,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { formatScore } from "../utils/format";
import type { TimeSeriesPoint } from "../utils/timeSeriesAggregation";
import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";
import { STATE_BOX_EMPTY } from "../ui/stateChrome";

const CHART_HEIGHT = 300;

type Audit5sPageProps = {
  pathname?: string;
};

export function Audit5sPage({ pathname }: Audit5sPageProps) {
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

  const { branches: branchOptions, loading: branchesLoading } = useQualityBranches(apiParams);

  const summaryParams = useMemo(
    () => ({
      branch: apiParams.branch,
      start_date: apiParams.date_start,
      end_date: apiParams.date_end,
    }),
    [apiParams.branch, apiParams.date_start, apiParams.date_end]
  );

  const { data, loading, requestProgress, error, reload } =
    useAudit5sSummary(summaryParams);
  const isRefreshing = loading && Boolean(data);
  const items = data?.list_audits ?? [];

  const areaChart = useMemo(() => aggregateAudit5sByArea(items), [items]);
  const scoreChart = useMemo(
    () =>
      aggregateAudit5sScoreByPeriod(items, dateStart, dateEnd, granularity),
    [items, dateStart, dateEnd, granularity]
  );

  const periodLabel = formatPeriodLabel(dateStart, dateEnd);

  const columns = useMemo<DataTableColumn<Audit5s>[]>(
    () => [
      {
        key: "date",
        header: "Data",
        render: (row) => formatDisplayDate(row.date),
      },
      {
        key: "evaluated_area",
        header: "Área",
        className: "dq-table__col--wide",
        render: (row) => row.evaluated_area ?? "—",
      },
      {
        key: "average_line_score",
        header: "Nota",
        className: "dq-table__col--numeric",
        render: (row) => formatScore(row.average_line_score),
      },
      {
        key: "branch",
        header: OPERATIONAL_UNIT_COLUMN_LABEL,
        render: (row) => formatOperationalUnitCode(row.branch),
      },
      {
        key: "auditor",
        header: "Auditor",
        render: (row) => row.auditor ?? "—",
      },
      {
        key: "audited",
        header: "Auditado",
        render: (row) => row.audited ?? "—",
      },
      {
        key: "shift",
        header: "Turno",
        render: (row) => row.shift ?? "—",
      },
      {
        key: "inspection_number",
        header: "Inspeção",
        render: (row) => row.inspection_number ?? "—",
      },
    ],
    []
  );

  const handleExportCsv = () => {
    if (items.length === 0) return;

    downloadCsv(
      "auditorias-5s.csv",
      [
        "Data",
        "Área",
        "Nota",
        "Unidade",
        "Auditor",
        "Auditado",
        "Turno",
        "Inspeção",
      ],
      items.map((row) => [
        formatDisplayDate(row.date),
        row.evaluated_area ?? "",
        String(row.average_line_score ?? ""),
        formatOperationalUnitCode(row.branch, ""),
        row.auditor ?? "",
        row.audited ?? "",
        row.shift ?? "",
        row.inspection_number ?? "",
      ])
    );
  };

  const handleChartDrillDown = (point: TimeSeriesPoint) => {
    if (!point.dateStart || !point.dateEnd) return;
    setDateStart(point.dateStart);
    setDateEnd(point.dateEnd);
  };

  const handleExportScoreCsv = () => {
    downloadChartSeriesCsv(
      "auditoria-5s-nota-media.csv",
      scoreChart.map((point) => ({
        periodo: point.periodo,
        value: point.value,
        valueLabel: "Nota média",
      }))
    );
  };

  return (
    <div className="dashboard-quality dashboard-page dq-print-root">
      <QualityPageHeader
        title="Auditoria 5S"
        subtitle="Notas e histórico de auditorias"
        currentPath={pathname ?? QUALITY_ROUTES.audit5s}
        filterState={filterState}
        printDisabled={loading && !data}
        onRefresh={reload}
        refreshing={loading && Boolean(data)}
        actions={
          <button
            type="button"
            className={`${GHOST_BTN} dq-no-print`}
            onClick={handleExportCsv}
            disabled={items.length === 0}
          >
            <Download size={16} />
            Exportar CSV
          </button>
        }
      />

      <div className="dq-no-print">
      <Audit5sFilters
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        selectedBranches={selectedBranches}
        branchOptions={branchOptions}
        branchesLoading={branchesLoading}
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
      />
      </div>

      <QualityStatusAlerts
        error={error}
        loading={loading}
        refreshing={isRefreshing}
        hasData={Boolean(data)}
        requestProgress={requestProgress}
        onRetry={reload}
        refreshTitle="Atualizando auditorias 5S"
        initialTitle="Carregando auditorias 5S"
        initialDescription="Buscando registros de auditoria para o período."
      />

      <section className="dq-kpi-grid" aria-busy={loading}>
        <KpiCard
          title="Nota média"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.audit5sScore}
          value={formatDashboardMetricValue(data?.average_score, data)}
          {...buildKpiGoalPresentation(
            periodLabel,
            data,
            undefined,
            { realizedValue: data?.average_score },
          )}
          icon={<Star size={22} />}
          loading={loading && !data}
        />
        <KpiCard
          title="Auditorias"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.audit5sCount}
          value={String(items.length || (loading ? "…" : 0))}
          subtitle="Registros no período filtrado"
          icon={<ClipboardCheck size={22} />}
          loading={loading && !data}
        />
      </section>

      <section className="dq-charts-grid" aria-busy={loading}>
        <ChartCard title="Nota média por área (top 8)">
          {areaChart.length === 0 && !loading ? (
            <div className={STATE_BOX_EMPTY}>Sem dados para o gráfico.</div>
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={areaChart} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" domain={[0, 5]} tick={{ fontSize: 12 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={120}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip
                  formatter={(value) => [formatScore(Number(value)), "Nota média"]}
                />
                <Bar dataKey="value" fill={CHART_COLORS[1]} radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard
          title="Evolução da nota média"
          hint="Clique em um ponto para filtrar a tabela pelo intervalo."
        >
          <ChartToolbar
            idPrefix="a5s-score"
            granularity={granularity}
            onGranularityChange={setGranularity}
            onExportCsv={handleExportScoreCsv}
            exportDisabled={scoreChart.length === 0}
          />

          {scoreChart.length === 0 && !loading ? (
            <div className={STATE_BOX_EMPTY}>Sem dados para o gráfico.</div>
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <LineChart
                data={scoreChart}
                onClick={(state) => {
                  const rawIndex = state?.activeTooltipIndex;
                  const index =
                    typeof rawIndex === "number" ? rawIndex : Number(rawIndex);
                  if (!Number.isFinite(index) || index < 0) return;
                  const point = scoreChart[index];
                  if (point) handleChartDrillDown(point);
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="periodo"
                  tick={{ fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis domain={[0, 5]} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => [formatScore(Number(value)), "Nota média"]}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={CHART_COLORS[0]}
                  strokeWidth={2}
                  dot={{ r: 4, cursor: "pointer" }}
                  activeDot={{ r: 6, cursor: "pointer" }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      <DataTableSection
        columnPreferencesKey="dashboard-quality:Audit5sPage:auditorias:v1"
        title="Auditorias"
        columns={columns}
        rows={items}
        rowKey={(row) => row.id}
        loading={loading && !data}
        emptyMessage="Nenhuma auditoria encontrada para os filtros."
        searchPlaceholder="Buscar setor, auditor, nota…"
      />
    </div>
  );
}