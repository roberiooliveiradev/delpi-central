import { useMemo } from "react";
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
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { KpiCard } from "../components/KpiCard";
import { Pagination } from "../components/Pagination";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { CHART_COLORS } from "../constants/chartColors";
import { QUALITY_ROUTES } from "../constants/routes";
import { useAudit5sSummary } from "../hooks/useQualityQueries";
import { useClientPagination } from "../hooks/useClientPagination";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityFilters } from "../hooks/useQualityFilters";
import type { Audit5s } from "../types/audit5s";
import {
  aggregateAudit5sByArea,
  aggregateAudit5sByMonth,
} from "../utils/chartAggregation";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import { formatScore } from "../utils/format";
const PAGE_SIZE = 20;
const CHART_HEIGHT = 300;

type Audit5sPageProps = {
  pathname?: string;
};

export function Audit5sPage({ pathname }: Audit5sPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
  } = useQualityFilters();

  const { branches, loading: branchesLoading } = useQualityBranches(apiParams);

  const summaryParams = useMemo(
    () => ({
      branch: apiParams.branch,
      start_date: apiParams.date_start,
      end_date: apiParams.date_end,
    }),
    [apiParams.branch, apiParams.date_start, apiParams.date_end]
  );

  const { data, loading, error, reload } = useAudit5sSummary(summaryParams);
  const items = data?.list_audits ?? [];

  const { page, setPage, slice, total } = useClientPagination(items, PAGE_SIZE);

  const areaChart = useMemo(() => aggregateAudit5sByArea(items), [items]);
  const monthChart = useMemo(() => aggregateAudit5sByMonth(items), [items]);

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
        header: "Filial",
        render: (row) => row.branch ?? "—",
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
        "Filial",
        "Auditor",
        "Auditado",
        "Turno",
        "Inspeção",
      ],
      items.map((row) => [
        formatDisplayDate(row.date),
        row.evaluated_area ?? "",
        String(row.average_line_score ?? ""),
        row.branch ?? "",
        row.auditor ?? "",
        row.audited ?? "",
        row.shift ?? "",
        row.inspection_number ?? "",
      ])
    );
  };

  return (
    <div className="dashboard-quality dashboard-page">
      <QualityPageHeader
        title="Auditoria 5S"
        subtitle="Notas e histórico de auditorias"
        currentPath={pathname ?? QUALITY_ROUTES.audit5s}
        onRefresh={reload}
        refreshing={loading && Boolean(data)}
        actions={
          <button
            type="button"
            className="dq-ghost-btn"
            onClick={handleExportCsv}
            disabled={items.length === 0}
          >
            <Download size={16} />
            Exportar CSV
          </button>
        }
      />

      <Audit5sFilters
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        branches={branches}
        branchesLoading={branchesLoading}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
      />

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
          title="Nota média"
          value={formatScore(data?.average_score)}
          subtitle={periodLabel}
          icon={<Star size={22} />}
          loading={loading && !data}
        />
        <KpiCard
          title="Auditorias"
          value={String(total || (loading ? "…" : 0))}
          subtitle="Registros no período filtrado"
          icon={<ClipboardCheck size={22} />}
          loading={loading && !data}
        />
      </section>

      <section className="dq-charts-grid" aria-busy={loading}>
        <ChartCard title="Nota média por área (top 8)">
          {areaChart.length === 0 && !loading ? (
            <div className="dq-state-box">Sem dados para o gráfico.</div>
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

        <ChartCard title="Evolução da nota média (mensal)">
          {monthChart.length === 0 && !loading ? (
            <div className="dq-state-box">Sem dados para o gráfico.</div>
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <LineChart data={monthChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 5]} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => [formatScore(Number(value)), "Nota média"]}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={CHART_COLORS[0]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </section>

      <section className="dq-table-section dq-card" aria-busy={loading}>
        <div className="dq-table-section__header">
          <h2 className="dq-section-title">Auditorias</h2>
          <span className="dq-table-section__meta">{total} registro(s)</span>
        </div>

        <DataTable
          columns={columns}
          rows={slice}
          rowKey={(row) => row.id}
          loading={loading && !data}
          emptyMessage="Nenhuma auditoria encontrada para os filtros."
        />

        {total > 0 ? (
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={total}
            onPageChange={setPage}
          />
        ) : null}
      </section>
    </div>
  );
}
