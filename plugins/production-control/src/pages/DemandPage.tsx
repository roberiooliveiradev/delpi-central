import {
  CHART_COLORS_DEPARTMENTAL,
  createDashboardKpiCard,
  createDashboardLoadingActivityCard,
  createDashboardStatusBadge,
  MultiTypeSeriesChart,
  NativeSelectField,
  formFieldShellBemClasses,
} from "@delpi/plugin-ui/index";
import { CalendarClock, Download, PackageSearch, TriangleAlert } from "lucide-react";
import { useEffect, useId, useMemo, useState } from "react";

import { ChartCard } from "../components/ChartCard";
import { DataTableSection } from "../components/dataTableUi";
import { DemandDetailModal } from "../components/DemandDetailModal";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { copy } from "../content/copy";
import { DEMAND_DEFAULT_FILTERS, useDemand, type DemandFilters } from "../hooks/useDemand";
import type { DemandLine, PpcBranch } from "../types";
import { downloadDemandCsv } from "../utils/demandCsv";
import { demandStatusBadge, demandStatusOptions } from "../utils/demandStatus";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";

const DEMAND_CHART_HEIGHT = 240;

const KpiCard = createDashboardKpiCard({ prefix: "ppc", labels: copy.kpi });
const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });
const fieldClasses = formFieldShellBemClasses("ppc");

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
};

export function DemandPage({ branch, search, status }: DemandPageProps) {
  const [filters, setFilters] = useState<DemandFilters>({
    ...DEMAND_DEFAULT_FILTERS,
    search: search ?? "",
    status: status ?? "",
  });
  const [searchDraft, setSearchDraft] = useState(filters.search);
  const [selected, setSelected] = useState<DemandLine | null>(null);
  const statusFieldId = useId();

  const { data, loading, refreshing, error, reload } = useDemand(branch, filters);
  const demand = copy.demand;

  useEffect(() => {
    setFilters((current) => ({ ...current, page: 1 }));
  }, [branch]);

  // A busca só vai ao BFF quando o usuário para de digitar.
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
  const statusOptions = useMemo(
    () => demandStatusOptions(data?.filters.statuses ?? []),
    [data?.filters.statuses],
  );

  const chartRows = useMemo(
    () =>
      (data?.horizon ?? []).map((bucket) => ({
        periodo: bucket.late
          ? demand.chart.lateLabel
          : demand.chart.weekLabel(formatIsoDate(bucket.start_date)),
        saldo: bucket.open_quantity,
      })),
    [data?.horizon, demand.chart],
  );

  const filtersActive =
    Boolean(filters.search) || Boolean(filters.status) || Boolean(filters.dueFrom) || Boolean(filters.dueTo);

  const columns = [
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
          {row.customer_order ? <span>{row.customer_order}</span> : null}
        </span>
      ),
    },
    {
      key: "order",
      header: demand.columns.order,
      render: (row: DemandLine) => `${row.sales_order}/${row.line_item}`,
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
                  series={[
                    {
                      dataKey: "saldo",
                      name: demand.chart.series,
                      fill: CHART_COLORS_DEPARTMENTAL[0],
                    },
                  ]}
                  chartType="column"
                  height={DEMAND_CHART_HEIGHT}
                  showLegend={false}
                  formatY={formatOpQuantity}
                  formatTooltipValue={formatOpQuantity}
                  margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
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
            columnPreferencesKey="production-control:demand:columns:v1"
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
                      setFilters({ ...DEMAND_DEFAULT_FILTERS });
                    }}
                  >
                    {demand.clearFilters}
                  </button>
                ) : null}
              </>
            }
            headerActions={
              <button
                type="button"
                className="ppc-ghost-btn"
                onClick={() => downloadDemandCsv(rows, demand.exportFileName(branch))}
                disabled={rows.length === 0}
              >
                <Download size={16} strokeWidth={1.75} aria-hidden />
                {demand.exportLabel}
              </button>
            }
          />
        </>
      ) : null}

      <DemandDetailModal line={selected} branch={branch} onClose={() => setSelected(null)} />
    </div>
  );
}
