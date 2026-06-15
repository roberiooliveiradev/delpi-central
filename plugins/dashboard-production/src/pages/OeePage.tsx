import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, CircleGauge, Download, Factory } from "lucide-react";

import { getProductionOee } from "../api/productionApi";
import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { OeeEvolutionChart } from "../components/OeeEvolutionChart";
import { OeeStatusBadge } from "../components/OeeStatusBadge";
import { ProductTypeBadge } from "../components/ProductTypeBadge";
import { PRODUCTION_ROUTES } from "../constants/routes";
import { useProductionFilters } from "../hooks/useProductionFilters";
import { useProductionOeeSeries } from "../hooks/useProductionOeeSeries";
import { useProductionResource } from "../hooks/useProductionResource";
import { useServerTable } from "../hooks/useServerTable";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import type {
  ProductionOeeAppointmentItem,
  ProductionOeeAppointmentStatus,
  ProductionOrderProductType,
} from "../types/production";
import type { ChartGranularity } from "../types/chart";
import { downloadOeeSeriesCsv } from "../utils/chartSeriesExport";
import { formatPeriodLabel, formatDisplayDate } from "../utils/dates";
import { formatProductionApiError } from "../utils/formatProductionApiError";
import { buildKpiGoalPresentation } from "../utils/goalDisplay";
import { formatInteger, formatPercent } from "../utils/format";
import { downloadOeeAppointmentsCsv } from "../utils/oeeExport";
import { navigateProduction } from "../utils/navigation";
import { buildOeeAppointmentPath } from "../constants/routes";
import { suggestGranularity } from "../utils/periodBuckets";

const PAGE_SIZE = 20;

type OeePageProps = {
  pathname?: string;
};

type StatusFilter = ProductionOeeAppointmentStatus | "";
type ProductTypeFilter = ProductionOrderProductType | "";

export function OeePage({ pathname }: OeePageProps) {
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
  const [productTypeFilter, setProductTypeFilter] = useState<ProductTypeFilter>("");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const serverTable = useServerTable({ pageSize: PAGE_SIZE });

  const oeeParams = useMemo(
    () => ({
      ...apiParams,
      status: statusFilter || undefined,
      product_type: productTypeFilter || undefined,
      page: serverTable.query.page,
      page_size: serverTable.query.pageSize,
      sort_by: serverTable.query.sortKey ?? undefined,
      sort_dir: serverTable.query.sortDirection,
    }),
    [apiParams, statusFilter, serverTable.query]
  );

  const { data, loading, error, reload } = useProductionResource(
    (signal) => getProductionOee(oeeParams, signal),
    [
      oeeParams.start_date,
      oeeParams.end_date,
      oeeParams.branch,
      oeeParams.status,
      oeeParams.product_type,
      oeeParams.page,
      oeeParams.sort_by,
      oeeParams.sort_dir,
    ]
  );

  const oeeSeries = useProductionOeeSeries({
    filters: apiParams,
    granularity,
  });

  useEffect(() => {
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  useEffect(() => {
    serverTable.resetPage();
  }, [apiParams.start_date, apiParams.end_date, apiParams.branch, statusFilter, productTypeFilter, serverTable.resetPage]);

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
    downloadOeeSeriesCsv("oee-evolucao.csv", oeeSeries.points);
  }, [oeeSeries.points]);

  const handleExportAppointmentsCsv = useCallback(async () => {
    setExportError(null);
    setExporting(true);

    try {
      const result = await getProductionOee({
        ...apiParams,
        status: statusFilter || undefined,
        product_type: productTypeFilter || undefined,
        page: 1,
        page_size: 1000,
        sort_by: serverTable.query.sortKey ?? undefined,
        sort_dir: serverTable.query.sortDirection,
      });

      downloadOeeAppointmentsCsv("oee-apontamentos.csv", result.appointments.items);
    } catch (reason) {
      setExportError(formatProductionApiError(reason));
    } finally {
      setExporting(false);
    }
  }, [apiParams, statusFilter, productTypeFilter, serverTable.query.sortKey, serverTable.query.sortDirection]);

  const appointmentColumns = useMemo<DataTableColumn<ProductionOeeAppointmentItem>[]>(
    () => [
      {
        key: "status",
        header: "Status",
        sortable: true,
        render: (row) => <OeeStatusBadge status={row.status} />,
      },
      {
        key: "branch",
        header: "Filial",
        sortable: true,
        render: (row) => row.branch ?? "—",
      },
      {
        key: "production_date",
        header: "Data",
        sortable: true,
        render: (row) => formatDisplayDate(row.production_date),
      },
      {
        key: "production_order",
        header: "OP",
        sortable: true,
        render: (row) => row.production_order ?? "—",
      },
      {
        key: "product_code",
        header: "Produto",
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
        key: "product_type",
        header: "Tipo",
        sortable: true,
        render: (row) => <ProductTypeBadge productType={row.product_type} />,
      },
      {
        key: "operator_code",
        header: "Operador",
        sortable: true,
        render: (row) => row.operator_code ?? "—",
      },
      {
        key: "work_center",
        header: "CT",
        sortable: true,
        render: (row) => row.work_center ?? "—",
      },
      {
        key: "operation",
        header: "Operação",
        sortable: true,
        render: (row) => row.operation ?? "—",
      },
      {
        key: "resource_name",
        header: "Recurso",
        sortable: true,
        render: (row) => row.resource_name || row.resource_code || "—",
      },
      {
        key: "oee_pct",
        header: "OEE (%)",
        className: "dp-table__col--numeric",
        sortable: true,
        render: (row) => formatPercent(row.oee_pct),
      },
      {
        key: "produced_qty",
        header: "Qtd",
        className: "dp-table__col--numeric",
        sortable: true,
        render: (row) => formatInteger(row.produced_qty),
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
    oeeSeries.reload();
  }, [reload, oeeSeries]);

  const handleAppointmentRowClick = useCallback(
    (row: ProductionOeeAppointmentItem) => {
      navigateProduction(buildOeeAppointmentPath(row.appointment_id), {
        ...filterState,
        branch: row.branch || filterState.branch,
      });
    },
    [filterState]
  );

  return (
    <div className="dashboard-production dashboard-page">
      <FilterBar
        title="OEE — Eficiência geral dos equipamentos"
        subtitle="Apontamentos de produção SH6010 (H6_ZEFICI) — média dos registros na faixa 0–199%"
        currentPath={pathname ?? PRODUCTION_ROUTES.oee}
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
          title="Carregando OEE de produção"
          description="Buscando resumo, evolução e apontamentos no período."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <section className="dp-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="OEE"
          value={formatPercent(data?.summary.oee_pct)}
          {...buildKpiGoalPresentation(
            `TOTVS · ${branchLabel} · ${periodLabel}`,
            data?.summary,
            formatPercent,
            { realizedValue: data?.summary.oee_pct }
          )}
          icon={<CircleGauge size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Apontamentos válidos"
          value={formatInteger(data?.summary.valid_appointments)}
          subtitle={`De ${formatInteger(data?.summary.total_appointments)} apontamentos`}
          icon={<Factory size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Fora da faixa"
          value={formatInteger(data?.summary.outlier_appointments)}
          subtitle={formatPercent(data?.summary.outlier_percentage)}
          icon={<Activity size={22} />}
          loading={isBusy && !data}
        />
      </section>

      <section className="dp-chart-section" aria-busy={oeeSeries.loading}>
        <ChartCard title="Evolução do OEE (%)" hint={temporalChartHint}>
          <ChartToolbar
            idPrefix="oee-detail"
            granularity={granularity}
            onGranularityChange={setGranularity}
            onExportCsv={handleExportChartCsv}
            exportDisabled={oeeSeries.points.length === 0}
          />

          {oeeSeries.error ? (
            <div className="dp-state dp-state--error" role="alert">
              <p>{oeeSeries.error}</p>
              <button
                className="dp-primary-btn"
                type="button"
                onClick={oeeSeries.reload}
              >
                Tentar novamente
              </button>
            </div>
          ) : null}

          {!oeeSeries.error &&
          (oeeSeries.points.length > 0 || oeeSeries.loading) ? (
            <OeeEvolutionChart
              data={oeeSeries.points}
              branch={branch || undefined}
              loading={oeeSeries.loading}
              onDrillDown={handleTemporalChartDrillDown}
            />
          ) : null}

          {!oeeSeries.error &&
          oeeSeries.points.length === 0 &&
          !oeeSeries.loading ? (
            <div className="dp-state-box">Sem dados para o gráfico no período.</div>
          ) : null}
        </ChartCard>
      </section>

      <div className="dp-ppm-toolbar" role="toolbar" aria-label="Filtros de apontamento">
        <div className="dp-ppm-toggle" role="group" aria-label="Tipo de produto">
          {[
            { value: "", label: "PA e PI" },
            { value: "PA", label: "PA" },
            { value: "PI", label: "PI" },
          ].map((option) => (
            <button
              key={option.value || "all-types"}
              type="button"
              className={`dp-ppm-toggle__btn${
                productTypeFilter === option.value ? " dp-ppm-toggle__btn--active" : ""
              }`}
              onClick={() => setProductTypeFilter(option.value as ProductTypeFilter)}
            >
              {option.label}
            </button>
          ))}
        </div>

        <div className="dp-ppm-toggle" role="group" aria-label="Status do apontamento">
          {[
            { value: "", label: "Todos" },
            { value: "valid", label: "Válidos" },
            { value: "outlier", label: "Fora da faixa" },
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
        title="Apontamentos de produção"
        hint="Clique em uma linha para abrir roteiro, estrutura e análise de tempos."
        columns={appointmentColumns}
        rows={data?.appointments.items ?? []}
        rowKey={(row) => String(row.appointment_id)}
        onRowClick={handleAppointmentRowClick}
        loading={loading && !(data?.appointments.items?.length)}
        refreshing={loading && Boolean(data?.appointments.items?.length)}
        emptyMessage="Nenhum apontamento no período."
        searchPlaceholder="Buscar OP, produto, CT, recurso…"
        getSearchText={(row) =>
          [
            row.branch,
            row.production_order,
            row.product_code,
            row.product_description,
            row.work_center,
            row.operation,
            row.operator_code,
            row.product_type,
            row.resource_code,
            row.resource_name,
            row.status,
          ]
            .filter(Boolean)
            .join(" ")
        }
        serverPagination={{
          page: data?.appointments.page ?? serverTable.query.page,
          pageSize: data?.appointments.page_size ?? PAGE_SIZE,
          total: data?.appointments.total ?? 0,
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
            onClick={() => void handleExportAppointmentsCsv()}
            disabled={exporting || (data?.appointments.total ?? 0) === 0}
          >
            <Download size={16} aria-hidden="true" />
            {exporting ? "Exportando…" : "Exportar CSV"}
          </button>
        }
      />
    </div>
  );
}
