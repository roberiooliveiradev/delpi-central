import { useMemo, useState } from "react";
import { Download, Lightbulb, Wallet } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "../components/ChartCard";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { KaizenFilters } from "../components/KaizenFilters";
import { KpiCard } from "../components/KpiCard";
import { Pagination } from "../components/Pagination";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { CHART_COLORS } from "../constants/chartColors";
import { QUALITY_ROUTES } from "../constants/routes";
import { useClientPagination } from "../hooks/useClientPagination";
import { useKaizenSummary } from "../hooks/useQualityQueries";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityFilters } from "../hooks/useQualityFilters";
import type { Kaizen } from "../types/kaizen";
import {
  aggregateKaizenByStatus,
  aggregateKaizenSavingsBySector,
} from "../utils/chartAggregation";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import { formatCurrency, formatDecimal } from "../utils/format";

const PAGE_SIZE = 20;
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
      ...apiParams,
      title: title || undefined,
      status: status || undefined,
    }),
    [apiParams, title, status]
  );

  const { data, loading, error, reload } = useKaizenSummary(summaryParams);
  const items = data?.list_kaizen ?? [];

  const { page, setPage, slice, total } = useClientPagination(items, PAGE_SIZE);

  const statusChart = useMemo(() => aggregateKaizenByStatus(items), [items]);
  const sectorChart = useMemo(
    () => aggregateKaizenSavingsBySector(items),
    [items]
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

  return (
    <div className="dashboard-quality dashboard-page">
      <QualityPageHeader
        title="Kaizens"
        subtitle="Melhorias implementadas e economia gerada"
        currentPath={pathname ?? QUALITY_ROUTES.kaizen}
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
          subtitle={periodLabel}
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

      <section className="dq-table-section dq-card" aria-busy={loading}>
        <div className="dq-table-section__header">
          <h2 className="dq-section-title">Lista de kaizens</h2>
          <span className="dq-table-section__meta">{total} registro(s)</span>
        </div>

        <DataTable
          columns={columns}
          rows={slice}
          rowKey={(row) => row.id}
          loading={loading && !data}
          emptyMessage="Nenhum kaizen encontrado para os filtros."
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
