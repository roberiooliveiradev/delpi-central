import { useEffect, useMemo, useState } from "react";
import { Download } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { NonconformityFilters } from "../components/NonconformityFilters";
import { Pagination } from "../components/Pagination";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { TotvsSourceBanner } from "../components/TotvsSourceBanner";
import { QUALITY_ROUTES } from "../constants/routes";
import { CHART_COLORS } from "../constants/chartColors";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useNonconformitiesChart } from "../hooks/useNonconformitiesChart";
import { useNonconformities } from "../hooks/useQualityQueries";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityFilters } from "../hooks/useQualityFilters";
import type { ChartGranularity, ChartSeriesPoint } from "../types/chart";
import type { Nonconformity, NonconformityType } from "../types/nonconformity";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate } from "../utils/dates";
import { formatDecimal } from "../utils/format";
import { downloadChartSeriesCsv } from "../utils/chartSeriesExport";
import { suggestGranularity } from "../utils/periodBuckets";

const PAGE_SIZE = 20;
const CHART_HEIGHT = 320;

type NonconformitiesPageProps = {
  pathname?: string;
};

function truncate(text: string | null, max = 80): string {
  if (!text) return "—";
  if (text.length <= max) return text;
  return `${text.slice(0, max)}…`;
}

export function NonconformitiesPage({ pathname }: NonconformitiesPageProps) {
  const [page, setPage] = useState(1);
  const [type, setType] = useState<NonconformityType>("all");
  const [status, setStatus] = useState("");
  const [itemCode, setItemCode] = useState("");
  const [description, setDescription] = useState("");
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

  const { branches, loading: branchesLoading } = useQualityBranches(apiParams);

  const debouncedStatus = useDebouncedValue(status);
  const debouncedItemCode = useDebouncedValue(itemCode);
  const debouncedDescription = useDebouncedValue(description);

  const listParams = useMemo(
    () => ({
      ...apiParams,
      type,
      status: debouncedStatus || undefined,
      item_code: debouncedItemCode || undefined,
      description: debouncedDescription || undefined,
      page,
      page_size: PAGE_SIZE,
    }),
    [
      apiParams,
      type,
      debouncedStatus,
      debouncedItemCode,
      debouncedDescription,
      page,
    ]
  );

  const { data, loading, error, reload } = useNonconformities(listParams);

  const chartFilters = useMemo(
    () => ({
      type,
      branch: apiParams.branch,
      date_start: apiParams.date_start,
      date_end: apiParams.date_end,
      status: debouncedStatus || undefined,
      item_code: debouncedItemCode || undefined,
      description: debouncedDescription || undefined,
    }),
    [
      type,
      apiParams.branch,
      apiParams.date_start,
      apiParams.date_end,
      debouncedStatus,
      debouncedItemCode,
      debouncedDescription,
    ]
  );

  const {
    points: chartData,
    truncated: chartTruncated,
    loading: chartLoading,
    error: chartError,
    reload: reloadChart,
  } = useNonconformitiesChart({
    filters: chartFilters,
    granularity,
  });

  useEffect(() => {
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  useEffect(() => {
    setPage(1);
  }, [
    apiParams.branch,
    apiParams.date_start,
    apiParams.date_end,
    type,
    status,
    itemCode,
    description,
  ]);

  const columns = useMemo<DataTableColumn<Nonconformity>[]>(
    () => [
      {
        key: "type_label",
        header: "Tipo",
        render: (row) => row.type_label ?? row.type_code ?? "—",
      },
      {
        key: "branch",
        header: "Filial",
        render: (row) => row.branch,
      },
      {
        key: "code",
        header: "Código",
        render: (row) => `${row.code}/${row.revision}`,
      },
      {
        key: "registered_date",
        header: "Registro",
        render: (row) => formatDisplayDate(row.registered_date),
      },
      {
        key: "occurrence_date",
        header: "Ocorrência",
        render: (row) => formatDisplayDate(row.occurrence_date),
      },
      {
        key: "status_label",
        header: "Status",
        render: (row) => row.status_label ?? row.status_code ?? "—",
      },
      {
        key: "item_code",
        header: "Item",
        render: (row) => row.item_code ?? "—",
      },
      {
        key: "description",
        header: "Descrição",
        className: "dq-table__col--wide",
        render: (row) => truncate(row.description),
      },
      {
        key: "returned_quantity",
        header: "Qtd. devolvida",
        className: "dq-table__col--numeric",
        render: (row) => formatDecimal(row.returned_quantity),
      },
    ],
    []
  );

  const handleExportCsv = () => {
    const items = data?.items ?? [];
    if (items.length === 0) return;

    downloadCsv(
      `nao-conformidades-totvs-pagina-${page}.csv`,
      [
        "Tipo",
        "Filial",
        "Código",
        "Revisão",
        "Registro",
        "Ocorrência",
        "Status",
        "Item",
        "Descrição",
        "Qtd devolvida",
      ],
      items.map((row) => [
        row.type_label ?? row.type_code,
        row.branch,
        row.code,
        row.revision,
        formatDisplayDate(row.registered_date),
        formatDisplayDate(row.occurrence_date),
        row.status_label ?? row.status_code ?? "",
        row.item_code ?? "",
        row.description ?? "",
        String(row.returned_quantity ?? ""),
      ])
    );
  };

  const handleRefresh = () => {
    reload();
    reloadChart();
  };

  const hasChartValues = chartData.some((point) => point.value > 0);

  const handleChartDrillDown = (point: ChartSeriesPoint) => {
    if (!point.dateStart || !point.dateEnd) return;
    setDateStart(point.dateStart);
    setDateEnd(point.dateEnd);
    setPage(1);
  };

  const handleExportChartCsv = () => {
    downloadChartSeriesCsv(
      "nao-conformidades-serie.csv",
      chartData.map((point) => ({
        periodo: point.periodo,
        value: point.value,
        valueLabel: "Qtd. devolvida",
      }))
    );
  };

  return (
    <div className="dashboard-quality dashboard-page dq-print-root">
      <QualityPageHeader
        title="Não conformidades"
        subtitle="Listagem analítica do Protheus (TOTVS)"
        currentPath={pathname ?? QUALITY_ROUTES.nonconformities}
        filterState={filterState}
        printDisabled={loading && !data}
        onRefresh={handleRefresh}
        refreshing={loading && Boolean(data)}
        actions={
          <button
            type="button"
            className="dq-ghost-btn dq-no-print"
            onClick={handleExportCsv}
            disabled={!data?.items.length}
          >
            <Download size={16} />
            Exportar CSV
          </button>
        }
      />

      <TotvsSourceBanner />

      <div className="dq-no-print">
      <NonconformityFilters
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        branches={branches}
        branchesLoading={branchesLoading}
        type={type}
        status={status}
        itemCode={itemCode}
        description={description}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onTypeChange={setType}
        onStatusChange={setStatus}
        onItemCodeChange={setItemCode}
        onDescriptionChange={setDescription}
      />
      </div>

      {error ? (
        <div className="dq-state dq-state--error" role="alert">
          <p>{error}</p>
          <button className="dq-primary-btn" type="button" onClick={handleRefresh}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      <section className="dq-chart-section" aria-busy={chartLoading}>
        <ChartCard
          title="Quantidade devolvida"
          hint={
            chartTruncated
              ? "Período extenso: exibindo os primeiros 60 intervalos. Clique em um ponto para filtrar a tabela."
              : "Agregado por data de registro no TOTVS. Clique em um ponto para filtrar a tabela."
          }
        >
          <ChartToolbar
            idPrefix="nc"
            granularity={granularity}
            onGranularityChange={setGranularity}
            onExportCsv={handleExportChartCsv}
            exportDisabled={chartData.length === 0}
          />

          {chartError ? (
            <div className="dq-state dq-state--error" role="alert">
              <p>{chartError}</p>
            </div>
          ) : null}

          {!chartError && chartData.length === 0 && !chartLoading ? (
            <div className="dq-state-box">Sem dados para o gráfico no período.</div>
          ) : null}

          {!chartError && (chartData.length > 0 || chartLoading) ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart
                data={chartData}
                onClick={(state) => {
                  const rawIndex = state?.activeTooltipIndex;
                  const index =
                    typeof rawIndex === "number" ? rawIndex : Number(rawIndex);
                  if (!Number.isFinite(index) || index < 0) return;
                  const point = chartData[index];
                  if (point) handleChartDrillDown(point);
                }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="periodo"
                  tick={{ fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => [
                    formatDecimal(Number(value)),
                    "Qtd. devolvida",
                  ]}
                />
                <Bar
                  dataKey="value"
                  fill={CHART_COLORS[2]}
                  radius={[6, 6, 0, 0]}
                  cursor="pointer"
                  name="Qtd. devolvida"
                />
              </BarChart>
            </ResponsiveContainer>
          ) : null}

          {!chartError && chartData.length > 0 && !hasChartValues && !chartLoading ? (
            <p className="dq-chart-card__hint dq-chart-card__hint--below">
              Nenhuma quantidade devolvida nos intervalos exibidos.
            </p>
          ) : null}
        </ChartCard>
      </section>

      <section className="dq-table-section dq-card" aria-busy={loading}>
        <div className="dq-table-section__header">
          <h2 className="dq-section-title">Registros</h2>
          {data ? (
            <span className="dq-table-section__meta">
              {data.total} registro(s) no período
            </span>
          ) : null}
        </div>

        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          rowKey={(row) => `${row.code}-${row.revision}-${row.branch}`}
          loading={loading && !data}
          emptyMessage="Nenhuma não conformidade encontrada para os filtros."
        />

        {data ? (
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onPageChange={setPage}
          />
        ) : null}
      </section>
    </div>
  );
}
