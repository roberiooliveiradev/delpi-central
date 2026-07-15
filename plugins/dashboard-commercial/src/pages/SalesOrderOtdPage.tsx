import { useCallback, useEffect, useMemo, useState } from "react";
import { CircleGauge, PackageCheck, Truck } from "lucide-react";
import { FieldLabel, useChartGranularitySelection } from "@delpi/plugin-ui/index";

import { getSalesOrderOtdPanel } from "../api/commercialApi";
import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/chartUi";
import type { DataTableColumn } from "../components/dataTableUi";
import { DataTableSection } from "../components/dataTableUi";
import { ExportActions } from "../components/ExportActions";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { SalesOrderOtdEvolutionChart } from "../components/SalesOrderOtdEvolutionChart";
import { SalesOrderOtdStatusBadge } from "../components/SalesOrderOtdStatusBadge";
import { TotvsSourceBanner } from "../components/TotvsSourceBanner";
import { COMMERCIAL_ROUTES } from "../constants/routes";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useCommercialFilters } from "../hooks/useCommercialFilters";
import { useCommercialResource } from "../hooks/useCommercialResource";
import { useCommercialSalesOrderOtdSeries } from "../hooks/useCommercialSalesOrderOtdSeries";
import { useLoadingProgress, EMPTY_REQUEST_PROGRESS } from "../hooks/useSimulatedLoadingProgress";
import { useServerTable } from "../hooks/useServerTable";
import type {
  SalesOrderOtdLineItem,
  SalesOrderOtdLineStatus,
} from "../types/commercial";
import { resolveCommercialApiBranch } from "../utils/commercialClientFilters";
import { formatPeriodLabel, formatDisplayDate } from "../utils/dates";
import { formatCommercialApiError } from "../utils/formatCommercialApiError";
import {
  buildKpiGoalPresentation,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { formatInteger, formatPercent } from "../utils/format";
import { navigateCommercial } from "../utils/navigation";
import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
  normalizeOperationalUnitCode,
} from "../utils/operationalUnitLabels";
import { buildSalesOrderOtdLinePath } from "../utils/routeParser";
import {
  downloadSalesOrderOtdSeriesCsv,
  exportSalesOrderOtdLinesExcel,
  exportSalesOrderOtdLinesPdf,
} from "../utils/salesOrderOtdExport";
import { STATE_BOX_EMPTY } from "../ui/stateChrome";

const PAGE_SIZE = 20;

type SalesOrderOtdPageProps = {
  pathname?: string;
};

type StatusFilter = SalesOrderOtdLineStatus | "";

export function SalesOrderOtdPage({ pathname }: SalesOrderOtdPageProps) {
  const {
    dateStart,
    dateEnd,
    competence,
    branches,
    customerSegment,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    setCustomerSegment,
    apiParams,
    filterState,
  } = useCommercialFilters();

  const { granularity, setGranularity } = useChartGranularitySelection(
    dateStart,
    dateEnd,
  );
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const serverTable = useServerTable({ pageSize: PAGE_SIZE });

  const panelParams = useMemo(
    () => ({
      ...apiParams,
      status: statusFilter || undefined,
      page: serverTable.query.page,
      page_size: serverTable.query.pageSize,
      sort_by: serverTable.query.sortKey ?? undefined,
      sort_dir: serverTable.query.sortDirection,
    }),
    [apiParams, statusFilter, serverTable.query]
  );

  const { data, loading, error, reload } = useCommercialResource(
    (signal) => getSalesOrderOtdPanel(panelParams, signal),
    [
      panelParams.start_date,
      panelParams.end_date,
      panelParams.branch,
      panelParams.customer_segment,
      panelParams.status,
      panelParams.page,
      panelParams.sort_by,
      panelParams.sort_dir,
    ]
  );

  const otdSeries = useCommercialSalesOrderOtdSeries({
    filters: apiParams,
    granularity,
  });

  useEffect(() => {
    serverTable.resetPage();
  }, [
    apiParams.start_date,
    apiParams.end_date,
    apiParams.branch,
    apiParams.customer_segment,
    statusFilter,
    serverTable.resetPage,
  ]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const selectedBranch = resolveCommercialApiBranch(branches);
  const branchLabel = selectedBranch
    ? formatOperationalUnitCode(selectedBranch, selectedBranch)
    : "Consolidado";

  const handleTemporalChartDrillDown = useCallback(
    (nextStart: string, nextEnd: string) => {
      setDateStart(nextStart);
      setDateEnd(nextEnd);
    },
    [setDateStart, setDateEnd]
  );

  const handleExportChartCsv = useCallback(() => {
    downloadSalesOrderOtdSeriesCsv("otd-pedidos-venda.csv", otdSeries.points);
  }, [otdSeries.points]);

  const fetchLinesForExport = useCallback(async () => {
    const result = await getSalesOrderOtdPanel({
      ...apiParams,
      status: statusFilter || undefined,
      page: 1,
      page_size: 1000,
      sort_by: serverTable.query.sortKey ?? undefined,
      sort_dir: serverTable.query.sortDirection,
    });
    return result.lines.items;
  }, [apiParams, statusFilter, serverTable.query.sortKey, serverTable.query.sortDirection]);

  const handleExportLinesExcel = useCallback(async () => {
    setExportError(null);
    setExporting(true);
    try {
      const items = await fetchLinesForExport();
      await exportSalesOrderOtdLinesExcel("otd-pedidos-venda", items);
    } catch (reason) {
      setExportError(formatCommercialApiError(reason));
    } finally {
      setExporting(false);
    }
  }, [fetchLinesForExport]);

  const handleExportLinesPdf = useCallback(async () => {
    setExportError(null);
    setExporting(true);
    try {
      const items = await fetchLinesForExport();
      await exportSalesOrderOtdLinesPdf("otd-pedidos-venda", items);
    } catch (reason) {
      setExportError(formatCommercialApiError(reason));
    } finally {
      setExporting(false);
    }
  }, [fetchLinesForExport]);

  const lineColumns = useMemo<DataTableColumn<SalesOrderOtdLineItem>[]>(
    () => [
      {
        key: "status",
        header: "Status",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.otd.table.status,
        sortable: true,
        render: (row) => <SalesOrderOtdStatusBadge status={row.status} />,
      },
      {
        key: "branch",
        header: OPERATIONAL_UNIT_COLUMN_LABEL,
        headerHint: COMMERCIAL_HELP_TOOLTIPS.otd.table.branch,
        sortable: true,
        render: (row) => formatOperationalUnitCode(row.branch),
      },
      {
        key: "order_number",
        header: "Pedido",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.otd.table.orderNumber,
        sortable: true,
        render: (row) => row.order_number ?? "—",
      },
      {
        key: "line_item",
        header: "Linha",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.otd.table.lineItem,
        sortable: true,
        render: (row) => row.line_item ?? "—",
      },
      {
        key: "product_code",
        header: "Produto",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.otd.table.productCode,
        sortable: true,
        render: (row) => row.product_code ?? "—",
      },
      {
        key: "product_description",
        header: "Descrição",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.otd.table.productDescription,
        className: "dc-table__col--wide",
        sortable: true,
        render: (row) => row.product_description ?? "—",
      },
      {
        key: "customer_name",
        header: "Cliente",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.otd.table.customerName,
        sortable: true,
        render: (row) => row.customer_name ?? row.customer_code ?? "—",
      },
      {
        key: "promised_date",
        header: "Entrega prometida",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.otd.table.promisedDate,
        sortable: true,
        render: (row) => formatDisplayDate(row.promised_date),
      },
      {
        key: "invoice_date",
        header: "Faturamento",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.otd.table.invoiceDate,
        sortable: true,
        render: (row) => formatDisplayDate(row.invoice_date) || "—",
      },
      {
        key: "days_diff",
        header: "Dias",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.otd.table.daysDiff,
        className: "dc-table__col--numeric",
        sortable: true,
        render: (row) => formatInteger(row.days_diff),
      },
    ],
    []
  );

  const isBusy = loading;
  const hasData = data !== null;
  const initialLoadingProgress = useLoadingProgress(
    loading && !hasData,
    EMPTY_REQUEST_PROGRESS
  );

  const handleRefresh = useCallback(() => {
    reload();
    otdSeries.reload();
  }, [reload, otdSeries]);

  const handleLineRowClick = useCallback(
    (row: SalesOrderOtdLineItem) => {
      navigateCommercial(
        buildSalesOrderOtdLinePath(
          normalizeOperationalUnitCode(row.branch),
          row.order_number,
          row.line_item,
          filterState
        )
      );
    },
    [filterState]
  );

  return (
    <div className="dashboard-commercial dashboard-page">
      <FilterBar
        title="OTD — Pedidos de venda"
        subtitle="Linhas SC6 no prazo vs. data prometida (faturadas e não faturadas)"
        currentPath={pathname ?? COMMERCIAL_ROUTES.salesOrderOtd}
        filterState={filterState}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        customerSegment={customerSegment}
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
        onCustomerSegmentChange={setCustomerSegment}
        onRefresh={handleRefresh}
        refreshing={loading && hasData}
      />

      <TotvsSourceBanner />

      {error ? (
        <div className="dc-state dc-state--error" role="alert">
          <p>{error}</p>
          <button className="dc-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {exportError ? (
        <div className="dc-state dc-state--warning" role="status">
          <p>{exportError}</p>
        </div>
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando OTD de pedidos de venda"
          description="Buscando resumo, evolução e linhas no período."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <section className="dc-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="OTD pedidos"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.otd.kpiOtd}
          value={formatDashboardMetricValue(
            data?.summary.sales_order_otd_pct,
            data?.summary
          )}
          {...buildKpiGoalPresentation(
            `TOTVS · ${branchLabel} · ${periodLabel}`,
            data?.summary,
            undefined,
            { realizedValue: data?.summary.sales_order_otd_pct }
          )}
          icon={<CircleGauge size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Linhas no prazo"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.otd.kpiOnTime}
          value={formatInteger(data?.summary.on_time_lines)}
          subtitle={`De ${formatInteger(data?.summary.total_lines)} linhas elegíveis`}
          icon={<PackageCheck size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title="Linhas atrasadas"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.otd.kpiLate}
          value={formatInteger(data?.summary.late_lines)}
          subtitle={formatPercent(data?.summary.late_percentage)}
          icon={<Truck size={22} />}
          loading={isBusy}
        />
      </section>

      <section className="dc-chart-section" aria-busy={otdSeries.loading}>
        <ChartCard
          title="Evolução do OTD (%)"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.otd.chartEvolution}
          hint="Clique em um ponto para filtrar o período."
        >
          <ChartToolbar
            idPrefix="sales-order-otd"
            granularity={granularity}
            onGranularityChange={setGranularity}
            onExportCsv={handleExportChartCsv}
            exportDisabled={otdSeries.points.length === 0}
          />

          {otdSeries.error ? (
            <div className="dc-state dc-state--error" role="alert">
              <p>{otdSeries.error}</p>
              <button
                className="dc-primary-btn"
                type="button"
                onClick={otdSeries.reload}
              >
                Tentar novamente
              </button>
            </div>
          ) : null}

          {!otdSeries.error &&
          (otdSeries.points.length > 0 || otdSeries.loading) ? (
            <SalesOrderOtdEvolutionChart
              data={otdSeries.points}
              branch={selectedBranch}
              loading={otdSeries.loading}
              onDrillDown={handleTemporalChartDrillDown}
            />
          ) : null}

          {!otdSeries.error &&
          otdSeries.points.length === 0 &&
          !otdSeries.loading ? (
            <div className={STATE_BOX_EMPTY}>Sem dados para o gráfico no período.</div>
          ) : null}
        </ChartCard>
      </section>

      <div className="dc-ppm-toolbar" role="toolbar" aria-label="Filtro de status">
        <div className="dc-ppm-toolbar__group">
          <FieldLabel
            label="Status da linha"
            hint={COMMERCIAL_HELP_TOOLTIPS.otd.filters.status}
            className="dc-field__label"
          />
          <div className="dc-ppm-toggle" role="group" aria-label="Status da linha">
            {[
              { value: "", label: "Todas" },
              { value: "on_time", label: "No prazo" },
              { value: "late", label: "Atrasadas" },
            ].map((option) => (
              <button
                key={option.value || "all"}
                type="button"
                className={`dc-ppm-toggle__btn${
                  statusFilter === option.value ? " dc-ppm-toggle__btn--active" : ""
                }`}
                onClick={() => setStatusFilter(option.value as StatusFilter)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <DataTableSection
        title="Linhas de pedido de venda"
        titleHint={COMMERCIAL_HELP_TOOLTIPS.otd.table.section}
        hint="Clique em uma linha para abrir o detalhe do pedido."
        columns={lineColumns}
        rows={data?.lines.items ?? []}
        rowKey={(row) =>
          `${row.branch}-${row.order_number}-${row.line_item}-${row.promised_date}`
        }
        onRowClick={handleLineRowClick}
        loading={loading && !(data?.lines.items?.length)}
        refreshing={loading && Boolean(data?.lines.items?.length)}
        emptyMessage="Nenhuma linha elegível no período."
        searchPlaceholder="Buscar pedido, produto, cliente…"
        searchHint={COMMERCIAL_HELP_TOOLTIPS.otd.table.search}
        getSearchText={(row) =>
          [
            formatOperationalUnitCode(row.branch, ""),
            row.order_number,
            row.line_item,
            row.product_code,
            row.product_description,
            row.customer_code,
            row.customer_name,
            row.status,
          ]
            .filter(Boolean)
            .join(" ")
        }
        serverPagination={{
          page: data?.lines.page ?? serverTable.query.page,
          pageSize: data?.lines.page_size ?? serverTable.query.pageSize,
          total: data?.lines.total ?? 0,
          onPageChange: serverTable.setPage,
          onPageSizeChange: serverTable.setPageSize,
        }}
        serverSort={{
          sortKey: serverTable.query.sortKey,
          sortDirection: serverTable.query.sortDirection,
          onSortChange: serverTable.handleSortChange,
        }}
        headerActions={
          <ExportActions
            exporting={exporting}
            disabled={(data?.lines.total ?? 0) === 0}
            onExportExcel={handleExportLinesExcel}
            onExportPdf={handleExportLinesPdf}
          />
        }
      />
    </div>
  );
}
