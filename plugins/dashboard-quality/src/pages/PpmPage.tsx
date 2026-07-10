import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, Factory, Truck } from "lucide-react";

import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { KpiCard } from "../components/KpiCard";
import { PpmCompareToggle } from "../components/PpmCompareToggle";
import { PpmEvolutionChart } from "../components/PpmEvolutionChart";
import { PpmTypeToggle } from "../components/PpmTypeToggle";
import { QualityFilters } from "../components/QualityFilters";
import { QualityPageHeader } from "../components/QualityPageHeader";
import { QualityStatusAlerts } from "../components/QualityStatusAlerts";
import { TotvsSourceBanner } from "../components/TotvsSourceBanner";
import { QUALITY_ROUTES, buildPpmDetailPath } from "../constants/routes";
import { getPpmChartReferenceLines } from "../constants/ppmReferenceLines";
import { usePpmChartSeries } from "../hooks/usePpmChartSeries";
import { usePpmPage } from "../hooks/usePpmPage";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityFilters } from "../hooks/useQualityFilters";
import { useChartGranularitySelection } from "@delpi/plugin-ui/index";
import type { PpmItem, PpmType } from "../types/ppm";
import { downloadCsv } from "../utils/csv";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import {
  buildKpiGoalPresentation,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { formatDecimal, formatCustomerRef, formatNonconformityCode } from "../utils/format";
import {
  downloadChartSeriesCsv,
  downloadDualPpmSeriesCsv,
} from "../utils/chartSeriesExport";
import { mergePpmSeries } from "../utils/mergePpmSeries";
import { navigateQuality } from "../utils/navigation";
import { savePpmDetailRecord } from "../utils/recordDetailStorage";
import { QUALITY_HELP_TOOLTIPS } from "../content/helpTooltips";
import { formatPpmProductScopeSuffix } from "../utils/ppmProductScope";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";

type PpmPageProps = {
  pathname?: string;
};

export function PpmPage({ pathname }: PpmPageProps) {
  const [ppmType, setPpmType] = useState<PpmType>("internal");
  const [compareChart, setCompareChart] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [tableSearch, setTableSearch] = useState("");

  const {
    dateStart,
    dateEnd,
    competence,
    branches: selectedBranches,
    ppmProductScope,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    setPpmProductScope,
    apiParams,
    ppmApiParams,
    filterState,
  } = useQualityFilters();

  const { granularity, setGranularity } = useChartGranularitySelection(
    dateStart,
    dateEnd,
  );

  const { branches: branchOptions, loading: branchesLoading } =
    useQualityBranches(apiParams);

  const { summary, page: tablePage, loading, refreshing, error, reload } =
    usePpmPage({
      type: ppmType,
      filters: ppmApiParams,
      page,
      pageSize,
    });

  const internalSeries = usePpmChartSeries({
    type: "internal",
    filters: ppmApiParams,
    granularity,
    enabled: compareChart || ppmType === "internal",
  });

  const externalSeries = usePpmChartSeries({
    type: "external",
    filters: ppmApiParams,
    granularity,
    enabled: compareChart || ppmType === "external",
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
  }, [ppmType, apiParams.branch, apiParams.date_start, apiParams.date_end, pageSize]);

  useEffect(() => {
    setPage(1);
  }, [tableSearch]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const tableRows = useMemo(() => {
    const items = tablePage?.items ?? [];
    const query = tableSearch.trim().toLowerCase();
    if (!query) return items;

    return items.filter((row) =>
      [
        formatOperationalUnitCode(row.branch, ""),
        formatNonconformityCode(row.code, row.code_display),
        row.customer_code,
        row.customer_store,
        row.customer_name,
        row.item_code,
        row.description,
        row.detailed_description,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [tablePage?.items, tableSearch]);

  const handlePpmRowClick = useCallback(
    (row: PpmItem) => {
      savePpmDetailRecord(row);
      navigateQuality(buildPpmDetailPath(), filterState);
    },
    [filterState]
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
        header: OPERATIONAL_UNIT_COLUMN_LABEL,
        headerHint: QUALITY_HELP_TOOLTIPS.table.branch,
        render: (row) => formatOperationalUnitCode(row.branch),
      },
      {
        key: "code",
        header: "Código Não Conformidade",
        render: (row) => formatNonconformityCode(row.code, row.code_display),
      },
      {
        key: "customer_code",
        header: "Cliente",
        render: (row) => formatCustomerRef(row.customer_code, row.customer_store),
      },
      {
        key: "customer_name",
        header: "Nome do cliente",
        className: "dq-table__col--wide",
        render: (row) => row.customer_name ?? "—",
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
        key: "detailed_description",
        header: "Descrição detalhada",
        className: "dq-table__col--wide",
        render: (row) => row.detailed_description ?? "—",
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
        "Unidade",
        "Código Não Conformidade",
        "Cliente",
        "Nome do cliente",
        "Revisão",
        "Item",
        "Descrição",
        "Descrição detalhada",
        "Qtd devolvida (un)",
      ],
      items.map((row) => [
        formatDisplayDate(row.registered_date),
        formatOperationalUnitCode(row.branch, ""),
        formatNonconformityCode(row.code, row.code_display),
        formatCustomerRef(row.customer_code, row.customer_store),
        row.customer_name ?? "",
        row.revision,
        row.item_code ?? "",
        row.description ?? "",
        row.detailed_description ?? "",
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
  const productScopeSuffix = formatPpmProductScopeSuffix(ppmProductScope);
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
        filterState={filterState}
        printDisabled={loading && !summary}
        onRefresh={handleRefresh}
        refreshing={refreshing}
        actions={
          <button
            type="button"
            className="dq-ghost-btn dq-no-print"
            onClick={handleExportCsv}
            disabled={!tablePage?.items.length}
          >
            <Download size={16} />
            Exportar CSV
          </button>
        }
      />

      <TotvsSourceBanner description="Consulta analítica de PPM (interno e externo)." />

      <QualityFilters
        idPrefix="ppm"
        className="dq-no-print"
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={selectedBranches}
        ppmProductScope={ppmProductScope}
        showPpmProductScope
        branchOptions={branchOptions}
        branchesLoading={branchesLoading}
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onPpmProductScopeChange={setPpmProductScope}
      />

      <div className="dq-ppm-toolbar dq-no-print">
        <PpmTypeToggle value={ppmType} onChange={setPpmType} />
        <PpmCompareToggle compare={compareChart} onChange={setCompareChart} />
      </div>

      <QualityStatusAlerts
        error={error}
        loading={loading}
        refreshing={refreshing}
        hasData={summary !== null || tablePage !== null}
        onRetry={handleRefresh}
        refreshTitle="Atualizando PPM"
        initialTitle="Carregando PPM"
        initialDescription="Buscando resumo e listagem de PPM para o período."
      />

      <section className="dq-kpi-grid dq-kpi-grid--single-row" aria-busy={isBusy}>
        <KpiCard
          title={`PPM ${typeLabel}${productScopeSuffix}`}
          titleHint={
            ppmType === "internal"
              ? QUALITY_HELP_TOOLTIPS.kpis.ppmInternal
              : QUALITY_HELP_TOOLTIPS.kpis.ppmExternal
          }
          value={formatDashboardMetricValue(summary?.ppm, summary)}
          {...buildKpiGoalPresentation(
            `Produzido: ${formatDecimal(summary?.total_produzido_un)} un · ${periodLabel}`,
            summary,
            undefined,
            { realizedValue: summary?.ppm },
          )}
          icon={
            ppmType === "internal" ? (
              <Factory size={22} />
            ) : (
              <Truck size={22} />
            )
          }
          loading={isBusy}
        />
        <KpiCard
          title="Total devolvido"
          titleHint={QUALITY_HELP_TOOLTIPS.kpis.ppmReturned}
          value={formatDecimal(summary?.total_devolvido_un)}
          subtitle={`Milheiro produzido: ${formatDecimal(summary?.total_produzido_milheiro)}`}
          icon={ppmType === "internal" ? <Factory size={22} /> : <Truck size={22} />}
          loading={isBusy}
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

      <DataTableSection
        title={`Registros de PPM ${typeLabel}`}
        titleHint={QUALITY_HELP_TOOLTIPS.table.section}
        hint={`${periodLabel} · clique na linha para ver o detalhe`}
        columns={columns}
        rows={tableRows}
        rowKey={(row) => `${row.code}-${row.revision}-${row.registered_date}`}
        loading={loading && !tablePage}
        refreshing={refreshing && Boolean(tablePage?.items.length)}
        onRowClick={handlePpmRowClick}
        searchPlaceholder="Buscar código, produto, cliente…"
        searchHint={QUALITY_HELP_TOOLTIPS.table.search}
        serverSearch={{
          value: tableSearch,
          onChange: setTableSearch,
        }}
        headerActions={
          <button
            type="button"
            className="dq-ghost-btn dq-no-print"
            onClick={handleExportCsv}
            disabled={!tablePage?.items.length}
          >
            <Download size={16} />
            Exportar CSV
          </button>
        }
        serverPagination={
          tablePage
            ? {
                page: tablePage.page,
                pageSize: tablePage.page_size,
                total: tablePage.total,
                onPageChange: setPage,
                onPageSizeChange: setPageSize,
              }
            : undefined
        }
      />
    </div>
  );
}