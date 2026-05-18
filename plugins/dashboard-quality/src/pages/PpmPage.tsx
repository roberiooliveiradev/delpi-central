import { useEffect, useMemo, useState } from "react";
import { Download, Factory, Truck } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "../components/ChartCard";
import { ChartGranularityToggle } from "../components/ChartGranularityToggle";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { KpiCard } from "../components/KpiCard";
import { Pagination } from "../components/Pagination";
import { PpmTypeToggle } from "../components/PpmTypeToggle";
import { QualityFilters } from "../components/QualityFilters";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { QUALITY_ROUTES } from "../constants/routes";
import { CHART_COLORS } from "../constants/chartColors";
import { usePpmChartSeries } from "../hooks/usePpmChartSeries";
import { usePpmPage } from "../hooks/usePpmPage";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityFilters } from "../hooks/useQualityFilters";
import type { ChartGranularity } from "../types/chart";
import type { PpmItem, PpmType } from "../types/ppm";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import { formatDecimal, formatPpm } from "../utils/format";
import { suggestGranularity } from "../utils/periodBuckets";

const CHART_HEIGHT = 320;

type PpmPageProps = {
  pathname?: string;
};

export function PpmPage({ pathname }: PpmPageProps) {
  const [ppmType, setPpmType] = useState<PpmType>("internal");
  const [page, setPage] = useState(1);
  const [granularity, setGranularity] = useState<ChartGranularity>("month");

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

  const { summary, page: tablePage, loading, refreshing, error, reload } =
    usePpmPage({
      type: ppmType,
      filters: apiParams,
      page,
    });

  const {
    points: chartData,
    loading: chartLoading,
    truncated: chartTruncated,
    error: chartError,
    reload: reloadChart,
  } = usePpmChartSeries({
    type: ppmType,
    filters: apiParams,
    granularity,
  });

  useEffect(() => {
    setPage(1);
  }, [ppmType, apiParams.branch, apiParams.date_start, apiParams.date_end]);

  useEffect(() => {
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const columns = useMemo<DataTableColumn<PpmItem>[]>(
    () => [
      {
        key: "registered_date",
        header: "Data",
        render: (row) => formatDisplayDate(row.registered_date),
      },
      {
        key: "branch",
        header: "Filial",
        render: (row) => row.branch,
      },
      {
        key: "code",
        header: "Código",
        render: (row) => row.code,
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
        render: (row) => row.description ?? "—",
      },
      {
        key: "returned_quantity_un",
        header: "Qtd. devolvida (un)",
        className: "dq-table__col--numeric",
        render: (row) => formatDecimal(row.returned_quantity_un),
      },
    ],
    []
  );

  const handleExportCsv = () => {
    const items = tablePage?.items ?? [];
    if (items.length === 0) return;

    downloadCsv(
      `ppm-${ppmType}-pagina-${page}.csv`,
      [
        "Data",
        "Filial",
        "Código",
        "Revisão",
        "Item",
        "Descrição",
        "Qtd devolvida (un)",
      ],
      items.map((row) => [
        formatDisplayDate(row.registered_date),
        row.branch,
        row.code,
        row.revision,
        row.item_code ?? "",
        row.description ?? "",
        String(row.returned_quantity_un ?? ""),
      ])
    );
  };

  const handleRefresh = () => {
    reload();
    reloadChart();
  };

  const isBusy = loading || refreshing;
  const isChartBusy = chartLoading || refreshing;
  const typeLabel = ppmType === "internal" ? "interno" : "externo";
  const hasChartValues = chartData.some((point) => point.ppm > 0);

  return (
    <div className="dashboard-quality dashboard-page">
      <QualityPageHeader
        title="PPM"
        subtitle={`Detalhamento ${typeLabel} — evolução do indicador e listagem`}
        currentPath={pathname ?? QUALITY_ROUTES.ppm}
        onRefresh={handleRefresh}
        refreshing={refreshing}
        actions={
          <button
            type="button"
            className="dq-ghost-btn"
            onClick={handleExportCsv}
            disabled={!tablePage?.items.length}
          >
            <Download size={16} />
            Exportar CSV
          </button>
        }
      />

      <QualityFilters
        idPrefix="ppm"
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        branches={branches}
        branchesLoading={branchesLoading}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
      />

      <div className="dq-ppm-toolbar">
        <PpmTypeToggle value={ppmType} onChange={setPpmType} />
      </div>

      {error ? (
        <div className="dq-state dq-state--error" role="alert">
          <p>{error}</p>
          <button className="dq-primary-btn" type="button" onClick={handleRefresh}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      <section className="dq-kpi-grid dq-kpi-grid--single-row" aria-busy={isBusy}>
        <KpiCard
          title={`PPM ${typeLabel}`}
          value={formatPpm(summary?.ppm)}
          subtitle={`Produzido: ${formatDecimal(summary?.total_produzido_un)} un · ${periodLabel}`}
          icon={
            ppmType === "internal" ? (
              <Factory size={22} />
            ) : (
              <Truck size={22} />
            )
          }
          loading={isBusy && !summary}
        />
        <KpiCard
          title="Total devolvido"
          value={formatDecimal(summary?.total_devolvido_un)}
          subtitle={`Milheiro produzido: ${formatDecimal(summary?.total_produzido_milheiro)}`}
          icon={ppmType === "internal" ? <Factory size={22} /> : <Truck size={22} />}
          loading={isBusy && !summary}
        />
      </section>

      <section className="dq-chart-section" aria-busy={isChartBusy}>
        <ChartCard
          title="Evolução do PPM"
          hint={
            chartTruncated
              ? "Período extenso: exibindo os primeiros 60 intervalos. Ajuste o filtro ou a granularidade."
              : "PPM calculado por intervalo (devolvido ÷ produzido), com a mesma regra do resumo."
          }
        >
          <div className="dq-chart-toolbar">
            <ChartGranularityToggle
              idPrefix="ppm"
              value={granularity}
              onChange={setGranularity}
            />
          </div>

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
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="periodo"
                  tick={{ fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => [
                    formatDecimal(Number(value)),
                    "PPM",
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="ppm"
                  stroke={CHART_COLORS[0]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="PPM"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : null}

          {!chartError && chartData.length > 0 && !hasChartValues && !chartLoading ? (
            <p className="dq-chart-card__hint dq-chart-card__hint--below">
              Todos os intervalos retornaram PPM zero no período filtrado.
            </p>
          ) : null}
        </ChartCard>
      </section>

      <section className="dq-table-section dq-card" aria-busy={isBusy}>
        <div className="dq-table-section__header">
          <h2 className="dq-section-title">Registros de PPM</h2>
        </div>

        <DataTable
          columns={columns}
          rows={tablePage?.items ?? []}
          rowKey={(row) => `${row.code}-${row.revision}-${row.registered_date}`}
          loading={loading && !tablePage}
        />

        {tablePage ? (
          <Pagination
            page={tablePage.page}
            pageSize={tablePage.page_size}
            total={tablePage.total}
            onPageChange={setPage}
          />
        ) : null}
      </section>
    </div>
  );
}
