import { useEffect, useMemo, useState } from "react";
import { Download, Factory, Truck } from "lucide-react";

import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import { DataTable, type DataTableColumn } from "../components/DataTable";
import { KpiCard } from "../components/KpiCard";
import { Pagination } from "../components/Pagination";
import { PpmCompareToggle } from "../components/PpmCompareToggle";
import { PpmEvolutionChart } from "../components/PpmEvolutionChart";
import { PpmTypeToggle } from "../components/PpmTypeToggle";
import { PrintReportButton } from "../components/PrintReportButton";
import { QualityFilters } from "../components/QualityFilters";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { QUALITY_ROUTES } from "../constants/routes";
import { getPpmChartReferenceLines } from "../constants/ppmReferenceLines";
import { usePpmChartSeries } from "../hooks/usePpmChartSeries";
import { usePpmPage } from "../hooks/usePpmPage";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityFilters } from "../hooks/useQualityFilters";
import type { ChartGranularity } from "../types/chart";
import type { PpmItem, PpmType } from "../types/ppm";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import { formatDecimal, formatPpm } from "../utils/format";
import {
  downloadChartSeriesCsv,
  downloadDualPpmSeriesCsv,
} from "../utils/chartSeriesExport";
import { mergePpmSeries } from "../utils/mergePpmSeries";
import { suggestGranularity } from "../utils/periodBuckets";

type PpmPageProps = {
  pathname?: string;
};

export function PpmPage({ pathname }: PpmPageProps) {
  const [ppmType, setPpmType] = useState<PpmType>("internal");
  const [compareChart, setCompareChart] = useState(false);
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

  const internalSeries = usePpmChartSeries({
    type: "internal",
    filters: apiParams,
    granularity,
  });

  const externalSeries = usePpmChartSeries({
    type: "external",
    filters: apiParams,
    granularity,
  });

  const activeSeries = ppmType === "internal" ? internalSeries : externalSeries;

  const compareChartData = useMemo(
    () => mergePpmSeries(internalSeries.points, externalSeries.points),
    [internalSeries.points, externalSeries.points]
  );

  const chartData = compareChart ? compareChartData : activeSeries.points;
  const chartLoading = compareChart
    ? internalSeries.loading || externalSeries.loading
    : activeSeries.loading;
  const chartTruncated = compareChart
    ? internalSeries.truncated || externalSeries.truncated
    : activeSeries.truncated;
  const chartError = compareChart
    ? internalSeries.error && externalSeries.error
      ? internalSeries.error
      : null
    : activeSeries.error;

  const referenceLines = useMemo(
    () =>
      getPpmChartReferenceLines(compareChart ? "compare" : ppmType),
    [compareChart, ppmType]
  );

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
    internalSeries.reload();
    externalSeries.reload();
  };

  const isBusy = loading || refreshing;
  const isChartBusy = chartLoading || refreshing;
  const typeLabel = ppmType === "internal" ? "interno" : "externo";
  const hasChartValues = compareChart
    ? compareChartData.some(
        (point) => point.ppmInternal > 0 || point.ppmExternal > 0
      )
    : activeSeries.points.some((point) => point.ppm > 0);

  const handleChartDrillDown = (dateStartValue: string, dateEndValue: string) => {
    setDateStart(dateStartValue);
    setDateEnd(dateEndValue);
    setPage(1);
  };

  const handleExportChartCsv = () => {
    if (compareChart) {
      downloadDualPpmSeriesCsv("ppm-comparativo-serie.csv", compareChartData);
      return;
    }

    downloadChartSeriesCsv(
      `ppm-${ppmType}-serie.csv`,
      activeSeries.points.map((point) => ({
        periodo: point.periodo,
        value: point.ppm,
        valueLabel: "PPM",
      }))
    );
  };

  const chartHint = compareChart
    ? chartTruncated
      ? "Comparativo interno × externo (período truncado nos primeiros 60 intervalos)."
      : "PPM interno e externo no mesmo período. Clique em um ponto para filtrar a tabela."
    : chartTruncated
      ? "Período extenso: exibindo os primeiros 60 intervalos. Ajuste o filtro ou a granularidade."
      : "PPM por intervalo (devolvido ÷ produzido). Clique em um ponto para filtrar a tabela.";

  return (
    <div className="dashboard-quality dashboard-page dq-print-root">
      <QualityPageHeader
        title="PPM"
        subtitle={
          compareChart
            ? "Comparativo interno × externo — evolução e listagem por tipo"
            : `Detalhamento ${typeLabel} — evolução do indicador e listagem`
        }
        currentPath={pathname ?? QUALITY_ROUTES.ppm}
        onRefresh={handleRefresh}
        refreshing={refreshing}
        actions={
          <>
            <PrintReportButton />
            <button
              type="button"
              className="dq-ghost-btn dq-no-print"
              onClick={handleExportCsv}
              disabled={!tablePage?.items.length}
            >
              <Download size={16} />
              Exportar CSV
            </button>
          </>
        }
      />

      <QualityFilters
        idPrefix="ppm"
        className="dq-no-print"
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        branches={branches}
        branchesLoading={branchesLoading}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
      />

      <div className="dq-ppm-toolbar dq-no-print">
        <PpmTypeToggle value={ppmType} onChange={setPpmType} />
        <PpmCompareToggle compare={compareChart} onChange={setCompareChart} />
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
        <ChartCard title={compareChart ? "PPM interno × externo" : "Evolução do PPM"} hint={chartHint}>
          <ChartToolbar
            idPrefix="ppm"
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

          {!chartError && (chartData.length > 0 || chartLoading) ? (
            <PpmEvolutionChart
              compare={compareChart}
              singleData={activeSeries.points}
              compareData={compareChartData}
              referenceLines={referenceLines}
              loading={chartLoading}
              onDrillDown={handleChartDrillDown}
            />
          ) : null}

          {!chartError && chartData.length > 0 && !hasChartValues && !chartLoading ? (
            <p className="dq-chart-card__hint dq-chart-card__hint--below">
              Todos os intervalos retornaram PPM zero no período filtrado.
            </p>
          ) : null}

          {referenceLines.length > 0 ? (
            <p className="dq-chart-card__hint dq-chart-card__hint--below dq-no-print">
              Linhas de referência: {referenceLines.map((line) => line.label).join(" e ")}.
              Configure em <code>ppmReferenceLines.ts</code> ou variáveis <code>VITE_DQ_PPM_*</code>.
            </p>
          ) : null}
        </ChartCard>
      </section>

      <section className="dq-table-section dq-card" aria-busy={isBusy}>
        <div className="dq-table-section__header">
          <h2 className="dq-section-title">
            Registros de PPM {typeLabel}
          </h2>
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
