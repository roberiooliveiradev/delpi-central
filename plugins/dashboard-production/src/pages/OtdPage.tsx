import { useCallback, useEffect, useMemo, useState } from "react";
import { CircleGauge, Download, Truck } from "lucide-react";

import { getProductionOtd } from "../api/productionApi";
import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { OtdEvolutionChart } from "../components/OtdEvolutionChart";
import { OtdStatusBadge } from "../components/OtdStatusBadge";
import { PRODUCTION_ROUTES } from "../constants/routes";
import { useProductionFilters } from "../hooks/useProductionFilters";
import { useProductionOtdSeries } from "../hooks/useProductionOtdSeries";
import { useProductionResource } from "../hooks/useProductionResource";
import { useServerTable } from "../hooks/useServerTable";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import type {
  ProductionOtdOrderItem,
  ProductionOtdOrderStatus,
} from "../types/production";
import type { ChartGranularity } from "../types/chart";
import { downloadOtdSeriesCsv } from "../utils/chartSeriesExport";
import { formatPeriodLabel, formatDisplayDate } from "../utils/dates";
import { formatProductionApiError } from "../utils/formatProductionApiError";
import { buildKpiGoalPresentation } from "../utils/goalDisplay";
import { formatInteger, formatPercent } from "../utils/format";
import { downloadOtdOrdersCsv } from "../utils/otdExport";
import { navigateProduction } from "../utils/navigation";
import { buildOtdOrderPath } from "../utils/routeParser";
import { suggestGranularity } from "../utils/periodBuckets";

const PAGE_SIZE = 20;

type OtdPageProps = {
  pathname?: string;
};

type StatusFilter = ProductionOtdOrderStatus | "";

export function OtdPage({ pathname }: OtdPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useProductionFilters();

  const [granularity, setGranularity] = useState<ChartGranularity>("month");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const serverTable = useServerTable({ pageSize: PAGE_SIZE });

  const otdParams = useMemo(
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

  const { data, loading, error, reload } = useProductionResource(
    (signal) => getProductionOtd(otdParams, signal),
    [
      otdParams.start_date,
      otdParams.end_date,
      otdParams.branch,
      otdParams.status,
      otdParams.page,
      otdParams.sort_by,
      otdParams.sort_dir,
    ]
  );

  const otdSeries = useProductionOtdSeries({
    filters: apiParams,
    granularity,
  });

  useEffect(() => {
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  useEffect(() => {
    serverTable.resetPage();
  }, [apiParams.start_date, apiParams.end_date, apiParams.branch, statusFilter, serverTable.resetPage]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const branchLabel = branch
    ? `Filial ${branch}`
    : "Consolidado (média das filiais)";

  const temporalChartHint = branch
    ? `Clique em um ponto para filtrar o período. Série da filial ${branch}.`
    : "Clique em um ponto para filtrar o período. Séries por filial 01 e 02.";

  const handleTemporalChartDrillDown = useCallback(
    (nextStart: string, nextEnd: string) => {
      setDateStart(nextStart);
      setDateEnd(nextEnd);
    },
    [setDateStart, setDateEnd]
  );

  const handleExportChartCsv = useCallback(() => {
    downloadOtdSeriesCsv("otd-evolucao.csv", otdSeries.points);
  }, [otdSeries.points]);

  const handleExportOrdersCsv = useCallback(async () => {
    setExportError(null);
    setExporting(true);

    try {
      const result = await getProductionOtd({
        ...apiParams,
        status: statusFilter || undefined,
        page: 1,
        page_size: 1000,
        sort_by: serverTable.query.sortKey ?? undefined,
        sort_dir: serverTable.query.sortDirection,
      });

      downloadOtdOrdersCsv("otd-ordens-producao.csv", result.orders.items);
    } catch (reason) {
      setExportError(formatProductionApiError(reason));
    } finally {
      setExporting(false);
    }
  }, [apiParams, statusFilter, serverTable.query.sortKey, serverTable.query.sortDirection]);

  const orderColumns = useMemo<DataTableColumn<ProductionOtdOrderItem>[]>(
    () => [
      {
        key: "status",
        header: "Status",
        sortable: true,
        render: (row) => <OtdStatusBadge status={row.status} />,
      },
      {
        key: "branch",
        header: "Filial",
        sortable: true,
        render: (row) => row.branch ?? "—",
      },
      {
        key: "production_order",
        header: "OP",
        sortable: true,
        render: (row) => row.production_order ?? "—",
      },
      {
        key: "order_number",
        header: "Nº OP",
        sortable: true,
        render: (row) => row.order_number ?? "—",
      },
      {
        key: "order_item",
        header: "Item",
        sortable: true,
        render: (row) => row.order_item ?? "—",
      },
      {
        key: "product_code",
        header: "Código",
        sortable: true,
        render: (row) => row.product_code ?? "—",
      },
      {
        key: "product_description",
        header: "Descrição",
        className: "dp-table__col--wide",
        sortable: true,
        render: (row) => row.product_description ?? "—",
      },
      {
        key: "due_date",
        header: "Previsto",
        sortable: true,
        render: (row) => formatDisplayDate(row.due_date),
      },
      {
        key: "finish_date",
        header: "Finalização",
        sortable: true,
        render: (row) => formatDisplayDate(row.finish_date),
      },
      {
        key: "days_diff",
        header: "Dias",
        className: "dp-table__col--numeric",
        sortable: true,
        render: (row) => formatInteger(row.days_diff),
      },
    ],
    []
  );

  const isBusy = loading;
  const hasData = data !== null;
  const initialFetchProgress = useTrackedSingleFetchProgress(loading && !hasData);
  const initialLoadingProgress = useLoadingProgress(
    loading && !hasData,
    initialFetchProgress
  );

  const handleRefresh = useCallback(() => {
    reload();
    otdSeries.reload();
  }, [reload, otdSeries]);

  const handleOrderRowClick = useCallback(
    (row: ProductionOtdOrderItem) => {
      navigateProduction(
        buildOtdOrderPath(row.production_order, row.branch, filterState, "PA"),
        filterState
      );
    },
    [filterState]
  );

  return (
    <div className="dashboard-production dashboard-page">
      <FilterBar
        title="OTD — Entrega no prazo"
        subtitle="OPs de produto acabado (PA) finalizadas no prazo — SC2010 × SB1010"
        currentPath={pathname ?? PRODUCTION_ROUTES.otd}
        filterState={filterState}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onRefresh={handleRefresh}
        refreshing={loading && hasData}
      />

      <DataSourceBanner />

      {error ? (
        <div className="dp-state dp-state--error" role="alert">
          <p>{error}</p>
          <button className="dp-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {exportError ? (
        <div className="dp-state dp-state--warning" role="status">
          <p>{exportError}</p>
        </div>
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando OTD de produção"
          description="Buscando resumo, evolução e ordens finalizadas no período."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <section className="dp-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="OTD"
          value={formatPercent(data?.summary.on_time_delivery_pct)}
          {...buildKpiGoalPresentation(
            `TOTVS · ${branchLabel} · ${periodLabel}`,
            data?.summary,
            formatPercent,
            { realizedValue: data?.summary.on_time_delivery_pct }
          )}
          icon={<CircleGauge size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="OPs no prazo"
          value={formatInteger(data?.summary.on_time_ops)}
          subtitle={`De ${formatInteger(data?.summary.total_ops_finished)} OPs finalizadas`}
          icon={<Truck size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="OPs em atraso"
          value={formatInteger(data?.summary.late_ops)}
          subtitle={formatPercent(data?.summary.late_percentage)}
          icon={<Truck size={22} />}
          loading={isBusy && !data}
        />
      </section>

      <section className="dp-charts-grid">
        <div className="dp-chart-section" aria-busy={otdSeries.loading}>
          <ChartCard
            title="Evolução do OTD (%)"
            hint={temporalChartHint}
          >
            <ChartToolbar
              idPrefix="otd-detail"
              granularity={granularity}
              onGranularityChange={setGranularity}
              onExportCsv={handleExportChartCsv}
              exportDisabled={otdSeries.points.length === 0}
            />

            {otdSeries.error ? (
              <div className="dp-state dp-state--error" role="alert">
                <p>{otdSeries.error}</p>
                <button
                  className="dp-primary-btn"
                  type="button"
                  onClick={otdSeries.reload}
                >
                  Tentar novamente
                </button>
              </div>
            ) : null}

            {!otdSeries.error &&
            (otdSeries.points.length > 0 || otdSeries.loading) ? (
              <OtdEvolutionChart
                data={otdSeries.points}
                branch={branch || undefined}
                loading={otdSeries.loading}
                onDrillDown={handleTemporalChartDrillDown}
              />
            ) : null}

            {!otdSeries.error &&
            otdSeries.points.length === 0 &&
            !otdSeries.loading ? (
              <div className="dp-state-box">Sem dados para o gráfico no período.</div>
            ) : null}
          </ChartCard>
        </div>
      </section>

      <div className="dp-ppm-toolbar" role="toolbar" aria-label="Filtro de status">
        <div className="dp-ppm-toggle" role="group" aria-label="Status da OP">
          {[
            { value: "", label: "Todas" },
            { value: "on_time", label: "No prazo" },
            { value: "late", label: "Atrasadas" },
          ].map((option) => (
            <button
              key={option.value || "all"}
              type="button"
              className={`dp-ppm-toggle__btn${
                statusFilter === option.value ? " dp-ppm-toggle__btn--active" : ""
              }`}
              onClick={() => setStatusFilter(option.value as StatusFilter)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <DataTableSection
        title="Ordens de produção"
        hint="Clique em uma linha para abrir o detalhe da OP e do produto."
        columns={orderColumns}
        rows={data?.orders.items ?? []}
        rowKey={(row) =>
          `${row.branch}-${row.production_order}-${row.order_item}-${row.finish_date}`
        }
        onRowClick={handleOrderRowClick}
        loading={loading && !(data?.orders.items?.length)}
        refreshing={loading && Boolean(data?.orders.items?.length)}
        emptyMessage="Nenhuma OP finalizada no período."
        searchPlaceholder="Buscar OP, produto, filial…"
        getSearchText={(row) =>
          [
            row.branch,
            row.production_order,
            row.order_number,
            row.order_item,
            row.product_code,
            row.product_description,
            row.status,
          ]
            .filter(Boolean)
            .join(" ")
        }
        serverPagination={{
          page: data?.orders.page ?? serverTable.query.page,
          pageSize: data?.orders.page_size ?? PAGE_SIZE,
          total: data?.orders.total ?? 0,
          onPageChange: serverTable.setPage,
        }}
        serverSort={{
          sortKey: serverTable.query.sortKey,
          sortDirection: serverTable.query.sortDirection,
          onSortChange: serverTable.handleSortChange,
        }}
        headerActions={
          <button
            type="button"
            className="dp-ghost-btn"
            onClick={() => void handleExportOrdersCsv()}
            disabled={exporting || (data?.orders.total ?? 0) === 0}
          >
            <Download size={16} aria-hidden="true" />
            {exporting ? "Exportando…" : "Exportar CSV"}
          </button>
        }
      />
    </div>
  );
}
