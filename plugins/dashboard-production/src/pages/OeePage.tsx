import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, CircleGauge, Factory } from "lucide-react";

import { getProductionOee } from "../api/productionApi";
import { ChartCard } from "../components/ChartCard";
import { ChartToolbar } from "../components/ChartToolbar";
import type { DataTableColumn } from "../components/DataTable";
import { DataTableSection } from "../components/DataTableSection";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { ExportActions } from "../components/ExportActions";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { OeeAppointmentToolbar } from "../components/OeeAppointmentToolbar";
import { OeeEvolutionChart } from "../components/OeeEvolutionChart";
import {
  formatEfficiencyBandsQuery,
  type ProductionEfficiencyBand,
} from "../constants/efficiencyBands";
import { DP_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD,
  PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
  PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
} from "../constants/businessRules";
import { PRODUCTION_ROUTES } from "../constants/routes";
import { useProductionFilters } from "../hooks/useProductionFilters";
import { useProductionOeeSeries } from "../hooks/useProductionOeeSeries";
import { useProductionResource } from "../hooks/useProductionResource";
import { useServerTable } from "../hooks/useServerTable";
import { resolveOeeAppointmentStatus } from "../utils/oeeAppointmentStatus";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import type {
  ProductionOeeAppointmentItem,
  ProductionOrderProductType,
} from "../types/production";
import type { ChartGranularity } from "../types/chart";
import { downloadOeeSeriesCsv } from "../utils/chartSeriesExport";
import { formatDisplayDate, formatDisplayTime, formatPeriodLabel } from "../utils/dates";
import { formatProductionApiError } from "../utils/formatProductionApiError";
import { formatCsvFilterValues } from "../utils/csvFilters";
import {
  buildOpFilterOptions,
  buildOperatorFilterOptions,
  buildWorkCenterFilterOptions,
} from "../utils/filterOptions";
import { buildKpiGoalPresentation } from "../utils/goalDisplay";
import { formatInteger, formatPercent, formatProductionQuantity } from "../utils/format";
import {
  exportOeeAppointmentsExcel,
  exportOeeAppointmentsPdf,
} from "../utils/oeeExport";
import { navigateProduction } from "../utils/navigation";
import { buildOeeAppointmentPath } from "../constants/routes";
import { suggestGranularity } from "../utils/periodBuckets";

const PAGE_SIZE = 20;

type OeePageProps = {
  pathname?: string;
};

type ProductTypeFilter = ProductionOrderProductType | "";

function formatOeePercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

function OeeAppointmentStatusCell({ row }: { row: ProductionOeeAppointmentItem }) {
  const status = resolveOeeAppointmentStatus(row);
  if (status === "verify") {
    return <span className="dp-appointment-badge dp-appointment-badge--danger">Verificar</span>;
  }
  if (status === "low") {
    return (
      <span className="dp-appointment-badge dp-appointment-badge--warning">Eficiência baixa</span>
    );
  }
  return <span className="dp-appointment-badge">OK</span>;
}

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
  const [efficiencyBandFilter, setEfficiencyBandFilter] = useState<ProductionEfficiencyBand[]>([]);
  const [productTypeFilter, setProductTypeFilter] = useState<ProductTypeFilter>("");
  const [selectedOps, setSelectedOps] = useState<string[]>([]);
  const [selectedOperators, setSelectedOperators] = useState<string[]>([]);
  const [selectedWorkCenters, setSelectedWorkCenters] = useState<string[]>([]);
  const [facetItems, setFacetItems] = useState<ProductionOeeAppointmentItem[]>([]);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const serverTable = useServerTable({ pageSize: PAGE_SIZE });

  const oeeParams = useMemo(
    () => ({
      ...apiParams,
      production_order: formatCsvFilterValues(selectedOps),
      operator_code: formatCsvFilterValues(selectedOperators),
      work_center: formatCsvFilterValues(selectedWorkCenters),
      efficiency_bands: formatEfficiencyBandsQuery(efficiencyBandFilter),
      product_type: productTypeFilter || undefined,
      page: serverTable.query.page,
      page_size: serverTable.query.pageSize,
      sort_by: serverTable.query.sortKey ?? undefined,
      sort_dir: serverTable.query.sortDirection,
    }),
    [
      apiParams,
      selectedOps,
      selectedOperators,
      selectedWorkCenters,
      efficiencyBandFilter,
      productTypeFilter,
      serverTable.query,
    ]
  );

  const { data, loading, error, reload } = useProductionResource(
    (signal) => getProductionOee(oeeParams, signal),
    [
      oeeParams.start_date,
      oeeParams.end_date,
      oeeParams.branch,
      oeeParams.production_order,
      oeeParams.operator_code,
      oeeParams.work_center,
      oeeParams.efficiency_bands,
      oeeParams.product_type,
      oeeParams.page,
      oeeParams.sort_by,
      oeeParams.sort_dir,
    ]
  );

  useEffect(() => {
    let cancelled = false;

    void getProductionOee({
      ...apiParams,
      page: 1,
      page_size: 1000,
    })
      .then((result) => {
        if (!cancelled) {
          setFacetItems(result.appointments.items);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFacetItems([]);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [apiParams.start_date, apiParams.end_date, apiParams.branch]);

  const opOptions = useMemo(() => buildOpFilterOptions(facetItems), [facetItems]);
  const operatorOptions = useMemo(
    () => buildOperatorFilterOptions(facetItems),
    [facetItems]
  );
  const workCenterOptions = useMemo(
    () => buildWorkCenterFilterOptions(facetItems),
    [facetItems]
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
  }, [
    apiParams.start_date,
    apiParams.end_date,
    apiParams.branch,
    selectedOps,
    selectedOperators,
    selectedWorkCenters,
    efficiencyBandFilter,
    productTypeFilter,
    serverTable.resetPage,
  ]);

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

  const fetchAppointmentsForExport = useCallback(async () => {
    const result = await getProductionOee({
      ...apiParams,
      production_order: formatCsvFilterValues(selectedOps),
      operator_code: formatCsvFilterValues(selectedOperators),
      work_center: formatCsvFilterValues(selectedWorkCenters),
      efficiency_bands: formatEfficiencyBandsQuery(efficiencyBandFilter),
      product_type: productTypeFilter || undefined,
      page: 1,
      page_size: 1000,
      sort_by: serverTable.query.sortKey ?? undefined,
      sort_dir: serverTable.query.sortDirection,
    });
    return result.appointments.items;
  }, [
    apiParams,
    selectedOps,
    selectedOperators,
    selectedWorkCenters,
    efficiencyBandFilter,
    productTypeFilter,
    serverTable.query.sortKey,
    serverTable.query.sortDirection,
  ]);

  const handleExportAppointmentsExcel = useCallback(async () => {
    setExportError(null);
    setExporting(true);
    try {
      const items = await fetchAppointmentsForExport();
      await exportOeeAppointmentsExcel("oee-apontamentos", items);
    } catch (reason) {
      setExportError(formatProductionApiError(reason));
    } finally {
      setExporting(false);
    }
  }, [fetchAppointmentsForExport]);

  const handleExportAppointmentsPdf = useCallback(async () => {
    setExportError(null);
    setExporting(true);
    try {
      const items = await fetchAppointmentsForExport();
      await exportOeeAppointmentsPdf("oee-apontamentos", items);
    } catch (reason) {
      setExportError(formatProductionApiError(reason));
    } finally {
      setExporting(false);
    }
  }, [fetchAppointmentsForExport]);

  const appointmentColumns = useMemo<DataTableColumn<ProductionOeeAppointmentItem>[]>(
    () => [
      {
        key: "production_date",
        header: "Data",
        headerHint: DP_HELP_TOOLTIPS.oee.table.productionDate,
        sortable: true,
        render: (row) => formatDisplayDate(row.production_date),
      },
      {
        key: "start_time",
        header: "Início",
        headerHint: DP_HELP_TOOLTIPS.oee.table.startTime,
        sortable: true,
        render: (row) => formatDisplayTime(row.start_time),
      },
      {
        key: "end_time",
        header: "Fim",
        headerHint: DP_HELP_TOOLTIPS.oee.table.endTime,
        sortable: true,
        render: (row) => formatDisplayTime(row.end_time),
      },
      {
        key: "produced_qty",
        header: "Qtd. apontada",
        headerHint: DP_HELP_TOOLTIPS.oee.table.producedQty,
        className: "dp-table__col--numeric",
        sortable: true,
        render: (row) => formatProductionQuantity(row.produced_qty, row.unit),
      },
      {
        key: "branch",
        header: "Filial",
        headerHint: DP_HELP_TOOLTIPS.oee.table.branch,
        sortable: true,
        render: (row) => row.branch ?? "—",
      },
      {
        key: "production_order",
        header: "OP",
        headerHint: DP_HELP_TOOLTIPS.oee.table.productionOrder,
        sortable: true,
        render: (row) => row.production_order ?? "—",
      },
      {
        key: "product_description",
        header: "Descrição produto",
        headerHint: DP_HELP_TOOLTIPS.oee.table.productDescription,
        className: "dp-table__col--wide",
        sortable: true,
        render: (row) => row.product_description?.trim() || row.product_code || "—",
      },
      {
        key: "work_center",
        header: "CT",
        headerHint: DP_HELP_TOOLTIPS.oee.table.workCenter,
        sortable: true,
        render: (row) => row.work_center ?? "—",
      },
      {
        key: "operator_code",
        header: "Operador",
        headerHint: DP_HELP_TOOLTIPS.oee.table.operatorCode,
        sortable: true,
        render: (row) => row.operator_code ?? "—",
      },
      {
        key: "oee_pct",
        header: "Eficiência",
        headerHint: DP_HELP_TOOLTIPS.oee.table.oeePct,
        className: "dp-table__col--numeric",
        sortable: true,
        render: (row) => formatOeePercent(row.oee_pct),
      },
      {
        key: "status",
        header: "Status",
        headerHint: DP_HELP_TOOLTIPS.oee.table.status,
        className: "dp-table__col--status",
        sortable: true,
        render: (row) => <OeeAppointmentStatusCell row={row} />,
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
        subtitle="Apontamentos OK da view fabril (EFICIENCIA_PERCENTUAL) — média na faixa 0–199%, mesmo escopo da eficiência fabril"
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
          titleHint={DP_HELP_TOOLTIPS.oee.kpiOee}
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
          title="Apontamentos"
          titleHint={DP_HELP_TOOLTIPS.oee.kpiAppointments}
          value={formatInteger(data?.summary.total_appointments)}
          subtitle={`${formatInteger(data?.summary.outlier_appointments)} a avaliar (Verificar)`}
          icon={<Factory size={22} />}
          loading={isBusy && !data}
        />
        <KpiCard
          title="Na faixa (indicador)"
          titleHint={DP_HELP_TOOLTIPS.oee.kpiValid}
          value={formatInteger(data?.summary.valid_appointments)}
          subtitle={formatPercent(data?.summary.oee_pct)}
          icon={<Activity size={22} />}
          loading={isBusy && !data}
        />
      </section>

      <section className="dp-chart-section" aria-busy={oeeSeries.loading}>
        <ChartCard
          title="Evolução do OEE (%)"
          titleHint={DP_HELP_TOOLTIPS.oee.chartEvolution}
          hint={temporalChartHint}
        >
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

      <OeeAppointmentToolbar
        productTypeFilter={productTypeFilter}
        efficiencyBandFilter={efficiencyBandFilter}
        selectedOps={selectedOps}
        selectedOperators={selectedOperators}
        selectedWorkCenters={selectedWorkCenters}
        opOptions={opOptions}
        operatorOptions={operatorOptions}
        workCenterOptions={workCenterOptions}
        onProductTypeFilterChange={setProductTypeFilter}
        onEfficiencyBandFilterChange={setEfficiencyBandFilter}
        onSelectedOpsChange={setSelectedOps}
        onSelectedOperatorsChange={setSelectedOperators}
        onSelectedWorkCentersChange={setSelectedWorkCenters}
        disabled={loading && !hasData}
      />

      <p className="dp-efficiency-legend dp-efficiency-legend--warning">
        Atenção: apontamentos com eficiência fora da faixa {PRODUCTION_EFFICIENCY_VALID_MIN_PCT}–
        {PRODUCTION_EFFICIENCY_VALID_MAX_PCT}% são desconsiderados no indicador de OEE (KPIs e gráficos)
        e aparecem na tabela como &quot;Verificar&quot;. Apontamentos na faixa válida com eficiência abaixo
        de {PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD}% aparecem como &quot;Eficiência baixa&quot; — abra o
        detalhe para verificar o motivo.
      </p>

      <DataTableSection
        title="Apontamentos de produção"
        titleHint={DP_HELP_TOOLTIPS.oee.table.section}
        hint="Clique em uma linha para abrir roteiro, estrutura e análise de tempos."
        columns={appointmentColumns}
        rows={data?.appointments.items ?? []}
        rowKey={(row) => String(row.appointment_id)}
        onRowClick={handleAppointmentRowClick}
        getRowClassName={(row) => {
          const status = resolveOeeAppointmentStatus(row);
          if (status === "verify") return "dp-row dp-row--verify";
          if (status === "low") return "dp-row dp-row--low-efficiency";
          return undefined;
        }}
        loading={loading && !(data?.appointments.items?.length)}
        refreshing={loading && Boolean(data?.appointments.items?.length)}
        emptyMessage="Nenhum apontamento no período."
        searchPlaceholder="Buscar OP, produto, CT, operador…"
        getSearchText={(row) =>
          [
            row.branch,
            row.production_order,
            row.product_code,
            row.product_description,
            row.work_center,
            row.operator_code,
            row.start_time,
            row.end_time,
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
          <ExportActions
            exporting={exporting}
            disabled={(data?.appointments.total ?? 0) === 0}
            onExportExcel={handleExportAppointmentsExcel}
            onExportPdf={handleExportAppointmentsPdf}
          />
        }
      />
    </div>
  );
}
