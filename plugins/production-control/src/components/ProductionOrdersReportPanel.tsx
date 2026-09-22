import { createDashboardFiltersKit, createDashboardKpiCard } from "@delpi/plugin-ui/index";
import { ClipboardList, Layers, Scale } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchProductionOrdersReport } from "../api/ppcApi";
import { SentenceHeaderDataTableSection, type DataTableColumn } from "./dataTableUi";
import { PpcLiquidLoading } from "./PpcLiquidLoading";
import { copy } from "../content/copy";
import {
  PRODUCTION_ORDERS_DEFAULT_FILTERS,
  isClosedProductionOrdersFilter,
  useProductionOrdersReport,
  type ProductionOrderTriFilter,
  type ProductionOrdersFilters,
} from "../hooks/useProductionOrdersReport";
import type { PpcBranch, ProductionOrderLine } from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { downloadProductionOrdersExcel } from "../utils/productionOrdersExcel";

const KpiCard = createDashboardKpiCard({
  prefix: "ppc",
  labels: copy.kpi,
});

const { FiltersRow, FilterInputField, FilterSelectField } = createDashboardFiltersKit({
  prefix: "ppc",
  labels: { filtersAriaLabel: copy.reports.productionOrders.filtersAria },
  portalScopeClassName: "dashboard-production-control",
});

const EXPORT_PAGE_SIZE = 200;
const EXPORT_MAX_PAGES = 40;

const TRI_OPTIONS: { value: ProductionOrderTriFilter; label: string }[] = [
  { value: "yes", label: copy.reports.productionOrders.triYes },
  { value: "no", label: copy.reports.productionOrders.triNo },
  { value: "all", label: copy.reports.productionOrders.triAll },
];

const SORT_COLUMNS: Record<string, string> = {
  production_order: "op",
  issue_date: "issue",
  due_date: "delivery",
  planned_qty: "qty",
};

async function fetchProductionOrdersForExport(params: {
  branch: PpcBranch;
  filters: ProductionOrdersFilters;
}): Promise<ProductionOrderLine[]> {
  const collected: ProductionOrderLine[] = [];
  let page = 1;
  let total = Number.POSITIVE_INFINITY;
  while (page <= EXPORT_MAX_PAGES && collected.length < total) {
    const payload = await fetchProductionOrdersReport({
      branch: params.branch,
      opKey: params.filters.opKey,
      productCode: params.filters.productCode,
      motherOnly: params.filters.motherOnly,
      openOnly: params.filters.openOnly,
      deliveryStart: params.filters.deliveryStart || null,
      deliveryEnd: params.filters.deliveryEnd || null,
      actualEndStart: isClosedProductionOrdersFilter(params.filters.openOnly)
        ? params.filters.actualEndStart || null
        : null,
      actualEndEnd: isClosedProductionOrdersFilter(params.filters.openOnly)
        ? params.filters.actualEndEnd || null
        : null,
      sort: params.filters.sort,
      page,
      pageSize: EXPORT_PAGE_SIZE,
    });
    collected.push(...payload.items);
    total = payload.pagination.total;
    if (!payload.items.length || collected.length >= total) break;
    page += 1;
  }
  return collected;
}

type Props = {
  branch: PpcBranch;
  onRefreshReady?: (reload: () => void) => void;
};

export function ProductionOrdersReportPanel({ branch, onRefreshReady }: Props) {
  const [filters, setFilters] = useState<ProductionOrdersFilters>({
    ...PRODUCTION_ORDERS_DEFAULT_FILTERS,
  });
  const [opKeyDraft, setOpKeyDraft] = useState(filters.opKey);
  const [productDraft, setProductDraft] = useState(filters.productCode);
  const [exporting, setExporting] = useState(false);
  const { data, loading, refreshing, error, reload } = useProductionOrdersReport(branch, filters);
  const reports = copy.reports.productionOrders;

  useEffect(() => {
    onRefreshReady?.(reload);
  }, [onRefreshReady, reload]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setFilters((current) => {
        if (current.opKey === opKeyDraft && current.productCode === productDraft) return current;
        return { ...current, opKey: opKeyDraft, productCode: productDraft, page: 1 };
      });
    }, 300);
    return () => window.clearTimeout(handle);
  }, [opKeyDraft, productDraft]);

  const patch = (partial: Partial<ProductionOrdersFilters>) => {
    setFilters((current) => {
      const nextOpenOnly = partial.openOnly ?? current.openOnly;
      const leavingClosed =
        current.openOnly === "no" && nextOpenOnly !== "no";
      return {
        ...current,
        ...partial,
        ...(leavingClosed ? { actualEndStart: "", actualEndEnd: "" } : {}),
        page:
          partial.page ??
          (partial.sort !== undefined || partial.pageSize !== undefined ? 1 : current.page),
      };
    });
  };

  const handleExportExcel = useCallback(async () => {
    if (exporting) return;
    setExporting(true);
    try {
      const lines = await fetchProductionOrdersForExport({ branch, filters });
      await downloadProductionOrdersExcel(lines, branch, {
        includeFinishDate: isClosedProductionOrdersFilter(filters.openOnly),
      });
    } catch (err) {
      console.error("[ProductionOrdersReportPanel] excel export", err);
      window.alert(reports.exportError);
    } finally {
      setExporting(false);
    }
  }, [branch, exporting, filters, reports.exportError]);

  const closedOnly = isClosedProductionOrdersFilter(filters.openOnly);

  const columns = useMemo<DataTableColumn<ProductionOrderLine>[]>(
    () => [
      {
        key: "production_order",
        header: reports.columns.op,
        sortable: true,
        render: (row) => row.production_order,
      },
      {
        key: "product_code",
        header: reports.columns.product,
        render: (row) => row.product_code || "—",
      },
      {
        key: "issue_date",
        header: reports.columns.issueDate,
        sortable: true,
        render: (row) => formatIsoDate(row.issue_date),
      },
      {
        key: "planned_start_date",
        header: reports.columns.startDate,
        render: (row) => formatIsoDate(row.planned_start_date),
      },
      {
        key: "due_date",
        header: reports.columns.dueDate,
        sortable: true,
        render: (row) => formatIsoDate(row.due_date),
      },
      ...(closedOnly
        ? [
            {
              key: "finish_date",
              header: reports.columns.finishDate,
              render: (row: ProductionOrderLine) => formatIsoDate(row.finish_date),
            },
          ]
        : []),
      {
        key: "planned_qty",
        header: reports.columns.quantity,
        sortable: true,
        align: "right" as const,
        render: (row) => formatOpQuantity(row.planned_qty),
      },
      {
        key: "pending_qty",
        header: reports.columns.balance,
        align: "right" as const,
        render: (row) => formatOpQuantity(row.pending_qty),
      },
      {
        key: "observation",
        header: reports.columns.observation,
        render: (row) => row.observation || "—",
      },
    ],
    [closedOnly, reports.columns],
  );

  const rows = data?.items ?? [];
  const summary = data?.summary;
  const canExport = (summary?.order_count ?? rows.length) > 0;
  const sortBase = filters.sort.replace(/_asc$|_desc$/, "");

  return (
    <section className="ppc-reports-detail" aria-label={reports.tableTitle}>
      {loading && !data ? <PpcLiquidLoading /> : null}

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error || copy.reports.loadError}
        </div>
      ) : null}

      {data ? (
        <>
          <FiltersRow variant="extended">
            <FilterInputField
              label={reports.opKeyLabel}
              hint={reports.opKeyHint}
              type="search"
              value={opKeyDraft}
              onChange={setOpKeyDraft}
              placeholder={reports.opKeyPlaceholder}
            />
            <FilterInputField
              label={reports.productLabel}
              hint={reports.productHint}
              type="search"
              value={productDraft}
              onChange={setProductDraft}
              placeholder={reports.productPlaceholder}
            />
            <FilterSelectField
              label={reports.openLabel}
              hint={reports.openHint}
              value={filters.openOnly}
              onChange={(value) => patch({ openOnly: value as ProductionOrderTriFilter, page: 1 })}
              options={TRI_OPTIONS}
            />
            <FilterSelectField
              label={reports.motherLabel}
              hint={reports.motherHint}
              value={filters.motherOnly}
              onChange={(value) => patch({ motherOnly: value as ProductionOrderTriFilter, page: 1 })}
              options={TRI_OPTIONS}
            />
            <FilterInputField
              label={reports.deliveryStartLabel}
              hint={reports.deliveryHint}
              type="date"
              value={filters.deliveryStart}
              onChange={(value) => patch({ deliveryStart: value, page: 1 })}
            />
            <FilterInputField
              label={reports.deliveryEndLabel}
              hint={reports.deliveryHint}
              type="date"
              value={filters.deliveryEnd}
              onChange={(value) => patch({ deliveryEnd: value, page: 1 })}
            />
            {closedOnly ? (
              <>
                <FilterInputField
                  label={reports.finishStartLabel}
                  hint={reports.finishHint}
                  type="date"
                  value={filters.actualEndStart}
                  onChange={(value) => patch({ actualEndStart: value, page: 1 })}
                />
                <FilterInputField
                  label={reports.finishEndLabel}
                  hint={reports.finishHint}
                  type="date"
                  value={filters.actualEndEnd}
                  onChange={(value) => patch({ actualEndEnd: value, page: 1 })}
                />
              </>
            ) : null}
          </FiltersRow>

          <div className="ppc-reports-kpis">
            <KpiCard
              title={reports.kpiOrders}
              value={String(summary?.order_count ?? 0)}
              icon={<ClipboardList size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title={reports.kpiQuantity}
              value={formatOpQuantity(summary?.planned_qty_sum ?? 0)}
              icon={<Layers size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title={reports.kpiBalance}
              value={formatOpQuantity(summary?.pending_qty_sum ?? 0)}
              icon={<Scale size={22} strokeWidth={1.75} />}
            />
          </div>

          <SentenceHeaderDataTableSection<ProductionOrderLine>
            title={reports.tableTitle}
            hideRecordsCount
            columns={columns}
            rows={rows}
            rowKey={(row) => `${row.branch}|${row.production_order}|${row.product_code}`}
            loading={loading || refreshing}
            emptyMessage={reports.empty}
            columnPreferencesKey="production-control:reports:production-orders:columns:v2"
            serverSort={{
              sortKey:
                sortBase === "op"
                  ? "production_order"
                  : sortBase === "issue"
                    ? "issue_date"
                    : sortBase === "delivery"
                      ? "due_date"
                      : sortBase === "qty"
                        ? "planned_qty"
                        : "production_order",
              sortDirection: filters.sort.endsWith("_desc") ? "desc" : "asc",
              onSortChange: (columnKey) => {
                const base = SORT_COLUMNS[columnKey] ?? "op";
                const nextDesc = filters.sort === `${base}_asc`;
                patch({ sort: `${base}_${nextDesc ? "desc" : "asc"}` });
              },
            }}
            serverPagination={{
              page: data.pagination.page,
              pageSize: data.pagination.page_size,
              total: data.pagination.total,
              onPageChange: (page) => setFilters((current) => ({ ...current, page })),
              onPageSizeChange: (pageSize) => patch({ pageSize }),
            }}
            excelExport={{
              onExport: () => void handleExportExcel(),
              disabled: !canExport || exporting,
              exporting,
              label: reports.exportLabel,
              exportingLabel: reports.exportExportingLabel,
            }}
          />
        </>
      ) : null}
    </section>
  );
}
