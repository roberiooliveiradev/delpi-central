import { createDashboardKpiCard } from "@delpi/plugin-ui/index";
import { Boxes, Package, Wallet } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchStockBalancesReport } from "../api/ppcApi";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";
import { PpcLiquidLoading } from "./PpcLiquidLoading";
import { copy } from "../content/copy";
import {
  STOCK_BALANCES_DEFAULT_FILTERS,
  useStockBalancesReport,
  type StockBalancesFilters,
} from "../hooks/useStockBalancesReport";
import type { PpcBranch, StockBalanceLine } from "../types";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { downloadStockBalancesExcel } from "../utils/stockBalancesExcel";

const KpiCard = createDashboardKpiCard({
  prefix: "ppc",
  labels: copy.kpi,
});

/** Teto alinhado ao BFF (`maxPageSize` / Query ≤ 5000) — uma chamada cobre o filtro. */
const EXPORT_PAGE_SIZE = 5000;

function formatMoney(value: number): string {
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

async function fetchStockBalancesForExport(params: {
  branch: PpcBranch;
  search: string;
  sort: string;
}): Promise<StockBalanceLine[]> {
  const payload = await fetchStockBalancesReport({
    branch: params.branch,
    search: params.search || undefined,
    sort: params.sort,
    page: 1,
    pageSize: EXPORT_PAGE_SIZE,
  });
  return payload.items;
}

type Props = {
  branch: PpcBranch;
  onRefreshReady?: (reload: () => void) => void;
};

/** Conteúdo do relatório de saldos — só monta quando o card está selecionado. */
export function StockBalancesReportPanel({ branch, onRefreshReady }: Props) {
  const [filters, setFilters] = useState<StockBalancesFilters>({
    ...STOCK_BALANCES_DEFAULT_FILTERS,
  });
  const [searchDraft, setSearchDraft] = useState(filters.search);
  const [exporting, setExporting] = useState(false);
  const { data, loading, refreshing, error, reload } = useStockBalancesReport(branch, filters);
  const reports = copy.reports;

  useEffect(() => {
    onRefreshReady?.(reload);
  }, [onRefreshReady, reload]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setFilters((current) =>
        current.search === searchDraft ? current : { ...current, search: searchDraft, page: 1 },
      );
    }, 300);
    return () => window.clearTimeout(handle);
  }, [searchDraft]);

  const patch = (partial: Partial<StockBalancesFilters>) => {
    setFilters((current) => ({
      ...current,
      ...partial,
      page:
        partial.page ??
        (partial.sort !== undefined || partial.pageSize !== undefined ? 1 : current.page),
    }));
  };

  const handleExportExcel = useCallback(async () => {
    if (exporting) return;
    setExporting(true);
    try {
      const lines = await fetchStockBalancesForExport({
        branch,
        search: filters.search,
        sort: filters.sort,
      });
      await downloadStockBalancesExcel(lines, branch);
    } catch (err) {
      console.error("[StockBalancesReportPanel] excel export", err);
      window.alert(reports.stockBalances.exportError);
    } finally {
      setExporting(false);
    }
  }, [branch, exporting, filters.search, filters.sort, reports.stockBalances]);

  const columns = useMemo<DataTableColumn<StockBalanceLine>[]>(
    () => [
      {
        key: "product_code",
        header: reports.columns.product,
        sortable: true,
        render: (row) => row.product_code,
      },
      {
        key: "description",
        header: reports.columns.description,
        render: (row) => row.description || "—",
      },
      {
        key: "warehouse",
        header: reports.columns.warehouse,
        render: (row) => row.warehouse,
      },
      {
        key: "quantity",
        header: reports.columns.quantity,
        sortable: true,
        align: "right" as const,
        render: (row) => formatOpQuantity(row.quantity),
      },
      {
        key: "unit_cost",
        header: reports.columns.unitCost,
        align: "right" as const,
        render: (row) => formatMoney(row.unit_cost),
      },
      {
        key: "stock_value",
        header: reports.columns.stockValue,
        sortable: true,
        align: "right" as const,
        render: (row) => formatMoney(row.stock_value),
      },
    ],
    [reports.columns],
  );

  const rows = data?.items ?? [];
  const summary = data?.summary;
  const canExport = (summary?.product_count ?? rows.length) > 0;

  return (
    <section className="ppc-reports-detail" aria-label={reports.stockBalances.tableTitle}>
      {loading && !data ? <PpcLiquidLoading /> : null}

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error || reports.loadError}
        </div>
      ) : null}

      {data ? (
        <>
          <div className="ppc-reports-kpis">
            <KpiCard
              title={reports.stockBalances.kpiProducts}
              value={String(summary?.product_count ?? 0)}
              icon={<Package size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title={reports.stockBalances.kpiQuantity}
              value={formatOpQuantity(summary?.total_quantity ?? 0)}
              icon={<Boxes size={22} strokeWidth={1.75} />}
            />
            <KpiCard
              title={reports.stockBalances.kpiValue}
              value={formatMoney(summary?.total_stock_value ?? 0)}
              icon={<Wallet size={22} strokeWidth={1.75} />}
            />
          </div>

          <DataTableSection<StockBalanceLine>
            title={reports.stockBalances.tableTitle}
            hint={reports.stockBalances.tableHint}
            columns={columns}
            rows={rows}
            rowKey={(row) => `${row.branch}|${row.warehouse}|${row.product_code}`}
            loading={loading || refreshing}
            emptyMessage={reports.stockBalances.empty}
            searchPlaceholder={reports.stockBalances.searchPlaceholder}
            columnPreferencesKey="production-control:reports:stock-balances:columns:v1"
            serverSearch={{ value: searchDraft, onChange: setSearchDraft }}
            serverSort={{
              sortKey: filters.sort.replace(/_asc$|_desc$/, ""),
              sortDirection: filters.sort.endsWith("_desc") ? "desc" : "asc",
              onSortChange: (columnKey) => {
                const base =
                  columnKey === "quantity" ||
                  columnKey === "stock_value" ||
                  columnKey === "product_code"
                    ? columnKey
                    : "product_code";
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
              label: reports.stockBalances.exportLabel,
              exportingLabel: reports.stockBalances.exportExportingLabel,
            }}
          />
        </>
      ) : null}
    </section>
  );
}
