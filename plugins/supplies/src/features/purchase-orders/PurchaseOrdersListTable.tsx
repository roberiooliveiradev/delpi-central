import { useMemo, useState, type CSSProperties } from "react";

import { buildPurchaseOrderDetailPath } from "../../app/pluginRoutes";
import {
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  ExcelExportButton,
  HelpTooltip,
  SuppliesCompactPagination,
  SuppliesDataListToolbar,
  SuppliesDataTable,
  SuppliesEntityLink,
  SuppliesSegmentToggle,
  SuppliesStatusBadge,
  SuppliesTableColumnVisibilityMenu,
  SuppliesTableFontSizeControls,
  spDataTableClassNames,
  usePersistedViewLayout,
  useTableColumnVisibility,
  useTableFontSize,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { PurchaseOrdersCards } from "./PurchaseOrdersCards";
import { downloadBlob, exportPurchaseOrders } from "./api";
import { PURCHASE_ORDERS_CONTENT as C } from "./content";
import {
  formatDatePtBr,
  formatMoneyBr,
  formatProductLabel,
  labelDeliveryStatus,
  nextServerSort,
  tableSortKey,
} from "./query";
import { purchaseOrdersColumnHelp } from "./purchaseOrdersColumnHelp";
import {
  PURCHASE_ORDERS_COLUMN_STORAGE_KEY,
  PURCHASE_ORDERS_TABLE_COLUMNS,
  PURCHASE_ORDERS_TABLE_EMPTY_FALLBACK_KEYS,
  PURCHASE_ORDERS_TABLE_FONT_SIZE_STORAGE_KEY,
  PURCHASE_ORDERS_VIEW_LAYOUT_STORAGE_KEY,
  type PurchaseOrderTableColumnKey,
} from "./purchaseOrdersTableConfig";
import type { PurchaseOrderListItem, PurchaseOrdersQuery } from "./types";
import { PURCHASE_ORDERS_PAGE_SIZE_OPTIONS } from "./types";

type PurchaseOrdersListTableProps = {
  items: PurchaseOrderListItem[];
  query: PurchaseOrdersQuery;
  total: number;
  loading: boolean;
  basePath: string;
  onPatchQuery: (patch: Partial<PurchaseOrdersQuery>) => void;
  onSelectRow: (item: PurchaseOrderListItem) => void;
};

function statusBadgeVariant(
  status: string | null | undefined,
): "danger" | "success" | "neutral" {
  if (status === "late") return "danger";
  if (status === "on_time") return "success";
  return "neutral";
}

export function PurchaseOrdersListTable({
  items,
  query,
  total,
  loading,
  basePath,
  onPatchQuery,
  onSelectRow,
}: PurchaseOrdersListTableProps) {
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const { layout, setLayout } = usePersistedViewLayout({
    storageKey: PURCHASE_ORDERS_VIEW_LAYOUT_STORAGE_KEY,
  });

  const columnPrefs = useTableColumnVisibility({
    storageKey: PURCHASE_ORDERS_COLUMN_STORAGE_KEY,
    columns: PURCHASE_ORDERS_TABLE_COLUMNS,
    emptyFallbackKeys: PURCHASE_ORDERS_TABLE_EMPTY_FALLBACK_KEYS,
  });

  const fontSizePrefs = useTableFontSize({
    storageKey: PURCHASE_ORDERS_TABLE_FONT_SIZE_STORAGE_KEY,
  });

  const columns = useMemo((): DataTableColumn<PurchaseOrderListItem>[] => {
    const byKey = new Map(
      PURCHASE_ORDERS_TABLE_COLUMNS.map((column) => [column.key, column]),
    );
    return columnPrefs.visibleKeys
      .map((key) => byKey.get(key as PurchaseOrderTableColumnKey))
      .filter((column): column is (typeof PURCHASE_ORDERS_TABLE_COLUMNS)[number] =>
        Boolean(column),
      )
      .map((column) => {
        const key = column.key as PurchaseOrderTableColumnKey;
        const numeric =
          key === "open_quantity" || key === "open_value"
            ? {
                align: "right" as const,
                className: spDataTableClassNames.colNumeric,
              }
            : {};
        return {
          key: column.key,
          header: column.label,
          headerHint: purchaseOrdersColumnHelp(key),
          sortable: true,
          ...numeric,
          interactive: key === "order_number",
          rowClick: key === "order_number" ? ("stop" as const) : undefined,
          render: (row: PurchaseOrderListItem) => {
            switch (key) {
              case "order_number": {
                const href = buildPurchaseOrderDetailPath(
                  row.branch,
                  row.order_number,
                  basePath,
                );
                const label = row.order_number || "—";
                return (
                  <SuppliesEntityLink
                    href={href}
                    title={C.openPcLinkTitle(label)}
                    className="sp-entity-link"
                    onNavigate={() => onSelectRow(row)}
                  >
                    {label}
                  </SuppliesEntityLink>
                );
              }
              case "order_item":
                return row.order_item || "—";
              case "product":
                return formatProductLabel(row.product_code, row.product_description);
              case "supplier":
                return row.supplier_name || row.supplier_code || "—";
              case "open_quantity":
                return row.open_quantity ?? "—";
              case "delivery":
                return formatDatePtBr(row.expected_delivery_date);
              case "status":
                return (
                  <SuppliesStatusBadge
                    label={labelDeliveryStatus(row.delivery_status)}
                    variant={statusBadgeVariant(row.delivery_status)}
                  />
                );
              case "open_value":
                return formatMoneyBr(row.open_value);
              default:
                return "—";
            }
          },
        };
      });
  }, [basePath, columnPrefs.visibleKeys, onSelectRow]);

  const totalPages = Math.max(1, Math.ceil(total / query.page_size) || 1);
  const visibleColumnCount = columns.length;

  const tableStyle = useMemo(
    (): CSSProperties =>
      ({
        "--delpi-ui-table-font-size": `${fontSizePrefs.fontSize}px`,
      }) as CSSProperties,
    [fontSizePrefs.fontSize],
  );

  const onExport = async () => {
    setExportError(null);
    setExporting(true);
    try {
      const blob = await exportPurchaseOrders(query);
      downloadBlob(blob, "purchase-orders.xlsx");
    } catch (err: unknown) {
      setExportError(err instanceof Error ? err.message : C.excelError);
    } finally {
      setExporting(false);
    }
  };

  const showCards = layout === "cards";

  return (
    <>
      <SuppliesDataListToolbar
        leading={
          <HelpTooltip
            content={SP_HELP.purchaseOrdersView}
            ariaLabel="Ajuda: modo Tabela ou Cards"
            wrap
            placement="bottom"
          >
            <SuppliesSegmentToggle
              ariaLabel={C.viewAriaLabel}
              idPrefix="purchase-orders-layout"
              size="sm"
              value={showCards ? "cards" : "table"}
              onChange={(value) => {
                if (value === "table" || value === "cards") setLayout(value);
              }}
              options={[
                { value: "table", label: C.viewTable },
                { value: "cards", label: C.viewCards },
              ]}
            />
          </HelpTooltip>
        }
        hint={
          <HelpTooltip
            content={SP_HELP.purchaseOrdersTableMeta}
            ariaLabel="Ajuda: metadados da tabela"
            wrap
            placement="bottom"
          >
            <span className="delpi-ui-section-hint-label">
              {C.tableMeta(visibleColumnCount, total)}
            </span>
          </HelpTooltip>
        }
        actions={
          <>
            <HelpTooltip
              content={SP_HELP.purchaseOrdersExcel}
              ariaLabel="Ajuda: exportar Excel"
              wrap
              placement="bottom"
            >
              <ExcelExportButton
                density="toolbar"
                onExport={() => void onExport()}
                disabled={loading || total === 0}
                exporting={exporting}
                label={C.excelLabel}
                exportingLabel={C.excelExporting}
              />
            </HelpTooltip>
            <SuppliesTableFontSizeControls
              fontSize={fontSizePrefs.fontSize}
              canIncrease={fontSizePrefs.canIncrease}
              canDecrease={fontSizePrefs.canDecrease}
              isDefault={fontSizePrefs.isDefault}
              onIncrease={fontSizePrefs.increase}
              onDecrease={fontSizePrefs.decrease}
              onReset={fontSizePrefs.reset}
            />
            <SuppliesTableColumnVisibilityMenu
              columns={columnPrefs.orderedColumns}
              visibility={columnPrefs.visibility}
              onToggleColumn={columnPrefs.setColumnVisible}
              onReset={columnPrefs.reset}
              onReorderColumns={columnPrefs.reorderColumns}
              labels={DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS}
            />
          </>
        }
      />

      {exportError ? (
        <p className="sp-purchase-orders__export-error" role="alert">
          {exportError}
        </p>
      ) : null}

      {showCards ? (
        <PurchaseOrdersCards items={items} basePath={basePath} onSelectRow={onSelectRow} />
      ) : (
        <div
          className="sp-list-table-region"
          role="region"
          aria-label={C.tableScrollRegion}
          tabIndex={0}
          style={tableStyle}
        >
          <SuppliesDataTable
            layout="section"
            columns={columns}
            rows={items}
            rowKey={(row) =>
              `${row.branch}-${row.order_number}-${row.order_item ?? ""}`
            }
            onRowClick={onSelectRow}
            getRowProps={(row) => ({
              "aria-label": `${C.detailTitle} ${row.order_number}`,
            })}
            loading={loading}
            sortKey={tableSortKey(query.sort_by)}
            sortDirection={query.sort_dir}
            onSortChange={(columnKey) => {
              const next = nextServerSort(query, columnKey);
              if (next) onPatchQuery(next);
            }}
            enableColumnReorder
            onColumnOrderChange={columnPrefs.applyVisibleOrder}
          />
        </div>
      )}

      <SuppliesCompactPagination
        page={query.page}
        pageSize={query.page_size}
        total={total}
        totalPages={totalPages}
        disabled={loading}
        pageSizeOptions={[...PURCHASE_ORDERS_PAGE_SIZE_OPTIONS]}
        onPageChange={(page) => onPatchQuery({ page })}
        onPageSizeChange={(pageSize) => onPatchQuery({ page_size: pageSize, page: 1 })}
      />
    </>
  );
}
