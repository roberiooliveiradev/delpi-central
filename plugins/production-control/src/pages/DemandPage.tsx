import {
  CHART_COLORS_DEPARTMENTAL,
  createDashboardKpiCard,
  createDashboardLoadingActivityCard,
  createDashboardStatusBadge,
  MultiTypeSeriesChart,
  NativeSelectField,
  createDashboardMultiSelectField,
  multiSelectBemClasses,
  formFieldShellBemClasses,
} from "@delpi/plugin-ui/index";
import { CalendarClock, PackageSearch, TriangleAlert } from "lucide-react";
import { useEffect, useId, useMemo, useState } from "react";

import { ChartCard } from "../components/ChartCard";
import { DataTableSection } from "../components/dataTableUi";
import { DemandDetailModal } from "../components/DemandDetailModal";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { copy } from "../content/copy";
import { DEMAND_DEFAULT_FILTERS, useDemand, type DemandFilters } from "../hooks/useDemand";
import type { DemandLine, PpcBranch } from "../types";
import { downloadDemandExcel } from "../utils/demandExcel";
import { demandOrderTableLabel } from "../utils/demandOrderLabel";
import { demandStatusBadge, demandStatusOptions } from "../utils/demandStatus";
import { canViewMywegNeeds, defaultDemandOrigin } from "../utils/demandOrigin";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";

const DEMAND_CHART_HEIGHT = 260;

const KpiCard = createDashboardKpiCard({ prefix: "ppc", labels: copy.kpi });
const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });
const fieldClasses = formFieldShellBemClasses("ppc");
const CustomerMultiSelect = createDashboardMultiSelectField({
  classNames: {
    ...multiSelectBemClasses("ppc"),
    root: "ppc-demand-customer-filter",
    fieldLabel: "ppc-demand-customer-filter__label",
  },
  portalScopeClassName: "dashboard-production-control",
  labels: {
    emptyLabel: copy.demand.customerAll,
    searchPlaceholder: copy.demand.customerSearch,
    selectVisible: copy.demand.customerSelectVisible,
    clear: copy.demand.customerClear,
    emptyOptions: copy.demand.customerEmpty,
    multipleSelected: copy.demand.customersSelected,
    searchAriaLabel: (label: string) => `Buscar em ${label}`,
  },
});

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.demand.loading,
  },
});

type DemandPageProps = {
  branch: PpcBranch;
  search: string | null;
  status: string | null;
  permissions?: readonly string[];
  isSuperadmin?: boolean;
};

function originBadgeLabel(source: string | undefined): string {
  return source === "myweg" ? copy.demand.originBadgeMyweg : copy.demand.originBadgeProtheus;
}

export function DemandPage({
  branch,
  search,
  status,
  permissions,
  isSuperadmin = false,
}: DemandPageProps) {
  const canViewMyweg = canViewMywegNeeds(permissions, isSuperadmin);
  const initialOrigin = defaultDemandOrigin(branch, canViewMyweg);
  const [filters, setFilters] = useState<DemandFilters>({
    ...DEMAND_DEFAULT_FILTERS,
    search: search ?? "",
    status: status ?? "",
    origin: initialOrigin,
  });
  const [searchDraft, setSearchDraft] = useState(filters.search);
  const [selected, setSelected] = useState<DemandLine | null>(null);
  const statusFieldId = useId();
  const originFieldId = useId();
  const customerFieldId = useId();

  const { data, loading, refreshing, error, reload } = useDemand(branch, filters);
  const demand = copy.demand;

  // Se o acesso a MyWEG for revogado na sessao, remove a origem restrita.
  // Ao trocar filial, App remonta a pagina, sem herdar filtros da filial anterior.
  useEffect(() => {
    if (canViewMyweg) return;
    setFilters((current) =>
      current.origin === "protheus"
        ? current
        : { ...current, origin: "protheus", customers: [], page: 1 },
    );
  }, [canViewMyweg]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setFilters((current) =>
        current.search === searchDraft ? current : { ...current, search: searchDraft, page: 1 },
      );
    }, 350);
    return () => window.clearTimeout(timer);
  }, [searchDraft]);

  const patch = (changes: Partial<DemandFilters>) =>
    setFilters((current) => ({ ...current, page: 1, ...changes }));

  const summary = data?.summary;
  const rows = data?.items ?? [];
  const customerOptions = data?.filters.customer_options ?? [];
  const showMywegUi = branch === "02" && canViewMyweg;
  const splitChart = Boolean(
    showMywegUi &&
      (data?.filters.origin === "both" || data?.filters.origin === "myweg") &&
      !data?.myweg?.myweg_skipped,
  );
  const statusOptions = useMemo(
    () => demandStatusOptions(data?.filters.statuses ?? []),
    [data?.filters.statuses],
  );
  const originOptions = useMemo(
    () => [
      { value: "both", label: demand.originAll },
      { value: "protheus", label: demand.originProtheus },
      { value: "myweg", label: demand.originMyweg },
    ],
    [demand.originAll, demand.originMyweg, demand.originProtheus],
  );

  const chartRows = useMemo(
    () =>
      (data?.horizon ?? []).map((bucket) => ({
        periodo: bucket.late
          ? demand.chart.lateLabel
          : demand.chart.weekLabel(formatIsoDate(bucket.start_date)),
        saldo: bucket.open_quantity,
        saldo_protheus: bucket.open_quantity_protheus ?? 0,
        saldo_myweg: bucket.open_quantity_myweg ?? 0,
      })),
    [data?.horizon, demand.chart],
  );

  const filtersActive =
    Boolean(filters.search) ||
    Boolean(filters.status) ||
    filters.customers.length > 0 ||
    Boolean(filters.dueFrom) ||
    Boolean(filters.dueTo) ||
    (showMywegUi && filters.origin !== "both");

  const mywegUpdatedLabel = useMemo(() => {
    const batch = data?.myweg?.batch;
    if (!batch) return null;
    const when = batch.collected_at || batch.collection_date || batch.collection_id;
    return when ? demand.mywegUpdated(formatIsoDate(String(when).slice(0, 10)) || String(when)) : null;
  }, [data?.myweg?.batch, demand]);

  const columns = [
    {
      key: "source",
      header: demand.columns.origin,
      render: (row: DemandLine) => (
        <span
          className={
            row.source === "myweg" ? "ppc-demand__origin ppc-demand__origin--myweg" : "ppc-demand__origin"
          }
        >
          {originBadgeLabel(row.source)}
        </span>
      ),
    },
    {
      key: "due_date",
      header: demand.columns.due,
      render: (row: DemandLine) => (
        <span className="ppc-demand__due">
          <strong>{formatIsoDate(row.due_date)}</strong>
          {row.days_late > 0 ? <span>{demand.lateBadge(row.days_late)}</span> : null}
        </span>
      ),
    },
    {
      key: "customer_name",
      header: demand.columns.customer,
      render: (row: DemandLine) => (
        <span className="ppc-demand__customer">
          <strong>{row.customer_name || "—"}</strong>
          <span>
            {[row.customer_code, row.customer_store].filter(Boolean).join(" / ") || row.customer_order || ""}
          </span>
        </span>
      ),
    },
    {
      key: "order",
      header: demand.columns.order,
      render: (row: DemandLine) => demandOrderTableLabel(row),
    },
    {
      key: "product_code",
      header: demand.columns.product,
      render: (row: DemandLine) => row.product_code || "—",
    },
    {
      key: "open_quantity",
      header: demand.columns.open,
      align: "right" as const,
      render: (row: DemandLine) => formatOpQuantity(row.open_quantity),
    },
    {
      key: "status",
      header: demand.columns.status,
      render: (row: DemandLine) => {
        const badge = demandStatusBadge(row.status);
        return <StatusBadge label={badge.label} variant={badge.variant} />;
      },
    },
  ];

  return (
    <div className="ppc-page-stack ppc-page-stack--demand">
      <PpcWorkspaceHeader
        title={demand.title}
        subtitle={demand.subtitle}
        branch={branch}
        subpluginId="demand"
        onRefresh={reload}
        refreshBusy={refreshing}
      />

      {loading ? (
        <LoadingCard title={demand.loading} description={demand.loadingHint} />
      ) : null}

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error || demand.loadError}
        </div>
      ) : null}

      {data ? (
        <>
          {showMywegUi && data.myweg?.op_coverage_complete === false ? (
            <div className="ppc-demand-banner" role="status">
              <p>{demand.opCoverageIncomplete}</p>
            </div>
          ) : null}

          {showMywegUi && data.myweg?.myweg_degraded ? (
            <div className="ppc-demand-banner" role="status">
              <p>{demand.mywegDegraded}</p>
            </div>
          ) : null}

          {showMywegUi && summary?.official_aggregate === false ? (
            <div className="ppc-demand-banner" role="status">
              <p>{demand.planningBanner}</p>
              {mywegUpdatedLabel ? <p>{mywegUpdatedLabel}</p> : null}
              {Number(data.myweg?.fiscal_reconciliation?.applied_un ?? 0) > 0 ? (
                <p>
                  {demand.fiscalReconciliationApplied(
                    new Intl.NumberFormat("pt-BR", {
                      maximumFractionDigits: 0,
                    }).format(Number(data.myweg?.fiscal_reconciliation?.applied_un ?? 0)),
                  )}
                </p>
              ) : null}
              {(data.myweg?.fiscal_pending_products?.length ?? 0) > 0 ? (
                <p>{demand.fiscalReconciliationPending}</p>
              ) : null}
              {data.myweg?.stock_incomplete || data.myweg?.stock_data_complete === false ? (
                <p>{demand.mywegIncomplete}</p>
              ) : null}
            </div>
          ) : null}

          <div className="ppc-demand-kpi-grid" aria-label={demand.kpi.sectionAria}>
            <KpiCard
              className="ppc-board-card"
              title={demand.kpi.openQuantity}
              titleHint={demand.kpi.openQuantityHint}
              icon={<PackageSearch size={20} strokeWidth={1.75} />}
              value={formatOpQuantity(summary?.open_quantity ?? 0)}
              footer={`${demand.kpi.lines(summary?.line_count ?? 0)} · ${demand.kpi.customers(
                summary?.customer_count ?? 0,
              )} · ${demand.kpi.products(summary?.product_count ?? 0)}`}
            />
            {showMywegUi && summary?.by_origin?.myweg ? (
              <KpiCard
                className="ppc-board-card"
                title={demand.kpi.mywegPlanned}
                titleHint={demand.kpi.mywegPlannedHint}
                icon={<PackageSearch size={20} strokeWidth={1.75} />}
                value={formatOpQuantity(summary.by_origin.myweg.open_quantity)}
                footer={demand.kpi.lines(summary.by_origin.myweg.line_count)}
              />
            ) : null}
            <KpiCard
              className="ppc-board-card"
              title={demand.kpi.lateLines}
              titleHint={demand.kpi.lateLinesHint}
              icon={<TriangleAlert size={20} strokeWidth={1.75} />}
              value={String(summary?.late_line_count ?? 0)}
            />
            <KpiCard
              className="ppc-board-card"
              title={demand.kpi.uncovered}
              titleHint={demand.kpi.uncoveredHint}
              icon={<PackageSearch size={20} strokeWidth={1.75} />}
              value={formatOpQuantity(summary?.uncovered_quantity ?? 0)}
              footer={demand.kpi.lines(summary?.at_risk_line_count ?? 0)}
            />
            <KpiCard
              className="ppc-board-card"
              title={demand.kpi.nextDue}
              titleHint={demand.kpi.nextDueHint}
              icon={<CalendarClock size={20} strokeWidth={1.75} />}
              value={summary?.next_due_date ? formatIsoDate(summary.next_due_date) : demand.kpi.none}
            />
          </div>

          <ChartCard
            title={demand.chart.title}
            hint={demand.chart.hint}
            className="ppc-demand-chart"
          >
            {chartRows.length === 0 ? (
              <p className="ppc-demand-chart__empty">{demand.chart.empty}</p>
            ) : (
              <div className="ppc-demand-chart__canvas">
                <MultiTypeSeriesChart
                  data={chartRows}
                  categoryKey="periodo"
                  series={
                    splitChart
                      ? [
                          {
                            dataKey: "saldo_protheus",
                            name: demand.chart.seriesProtheus,
                            fill: CHART_COLORS_DEPARTMENTAL[0],
                          },
                          {
                            dataKey: "saldo_myweg",
                            name: demand.chart.seriesMyweg,
                            fill: CHART_COLORS_DEPARTMENTAL[1],
                          },
                        ]
                      : [
                          {
                            dataKey: "saldo",
                            name: demand.chart.series,
                            fill: CHART_COLORS_DEPARTMENTAL[0],
                          },
                        ]
                  }
                  chartType={splitChart ? "stacked_bar" : "column"}
                  height={DEMAND_CHART_HEIGHT}
                  showLegend={splitChart}
                  showValueLabels={!splitChart}
                  formatY={formatOpQuantity}
                  formatTooltipValue={formatOpQuantity}
                  margin={{ top: 28, right: 8, left: 0, bottom: 0 }}
                />
              </div>
            )}
          </ChartCard>

          <DataTableSection<DemandLine>
            title={demand.tableTitle}
            hint={demand.tableHint}
            columns={columns}
            rows={rows}
            rowKey={(row) => row.id}
            loading={loading}
            refreshing={refreshing}
            emptyMessage={demand.empty}
            searchPlaceholder={demand.searchPlaceholder}
            columnPreferencesKey="production-control:demand:columns:v2"
            onRowClick={setSelected}
            serverSearch={{ value: searchDraft, onChange: setSearchDraft }}
            serverSort={{
              sortKey: filters.sort,
              sortDirection: filters.direction,
              onSortChange: (columnKey) =>
                patch({
                  sort: columnKey,
                  direction:
                    filters.sort === columnKey && filters.direction === "asc" ? "desc" : "asc",
                }),
            }}
            serverPagination={{
              page: data.pagination.page,
              pageSize: data.pagination.page_size,
              total: data.pagination.total,
              onPageChange: (page) => setFilters((current) => ({ ...current, page })),
              onPageSizeChange: (pageSize) => patch({ pageSize }),
            }}
            toolbarExtra={
              <>
                <CustomerMultiSelect
                  id={customerFieldId}
                  label={demand.customerLabel}
                  options={customerOptions}
                  selectedValues={filters.customers}
                  onChange={(customers) => patch({ customers })}
                  searchable
                  emptyLabel={demand.customerAll}
                  includeSelectedInOptions
                />
                {showMywegUi ? (
                  <NativeSelectField
                    id={originFieldId}
                    label={demand.originLabel}
                    value={filters.origin}
                    options={originOptions}
                    onChange={(value) => patch({ origin: value || "both" })}
                    classNames={fieldClasses}
                  />
                ) : null}
                <NativeSelectField
                  id={statusFieldId}
                  label={demand.columns.status}
                  value={filters.status}
                  options={statusOptions}
                  placeholderOption={demand.statusAll}
                  onChange={(value) => patch({ status: value })}
                  classNames={fieldClasses}
                />
                <label className="ppc-demand-filter">
                  <span>{demand.dueFromLabel}</span>
                  <input
                    type="date"
                    value={filters.dueFrom}
                    onChange={(event) => patch({ dueFrom: event.target.value })}
                  />
                </label>
                <label className="ppc-demand-filter">
                  <span>{demand.dueToLabel}</span>
                  <input
                    type="date"
                    value={filters.dueTo}
                    onChange={(event) => patch({ dueTo: event.target.value })}
                  />
                </label>
                {filtersActive ? (
                  <button
                    type="button"
                    className="ppc-ghost-btn"
                    onClick={() => {
                      setSearchDraft("");
                      setFilters({
                        ...DEMAND_DEFAULT_FILTERS,
                        origin: initialOrigin,
                      });
                    }}
                  >
                    {demand.clearFilters}
                  </button>
                ) : null}
              </>
            }
            excelExport={{
              onExport: () => downloadDemandExcel(rows, demand.exportFileName(branch)),
              disabled: rows.length === 0,
            }}
          />
        </>
      ) : null}

      <DemandDetailModal line={selected} branch={branch} onClose={() => setSelected(null)} />
    </div>
  );
}
