import { useMemo, type CSSProperties } from "react";

import {
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  SuppliesCompactPagination,
  SuppliesDataListToolbar,
  SuppliesDataTable,
  SuppliesStatusBadge,
  SuppliesTableColumnVisibilityMenu,
  SuppliesTableFontSizeControls,
  useTableColumnVisibility,
  useTableFontSize,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { PURCHASE_ORDERS_CONTENT as C } from "./content";
import {
  formatDatePtBr,
  formatMoneyBr,
  formatProductLabel,
  labelDeliveryStatus,
} from "./query";
import {
  PURCHASE_ORDERS_COLUMN_STORAGE_KEY,
  PURCHASE_ORDERS_TABLE_COLUMNS,
  PURCHASE_ORDERS_TABLE_EMPTY_FALLBACK_KEYS,
  PURCHASE_ORDERS_TABLE_FONT_SIZE_STORAGE_KEY,
  type PurchaseOrderTableColumnKey,
} from "./purchaseOrdersTableConfig";
import type { PurchaseOrderListItem, PurchaseOrdersQuery } from "./types";

type PurchaseOrdersListTableProps = {
  items: PurchaseOrderListItem[];
  query: PurchaseOrdersQuery;
  total: number;
  loading: boolean;
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

function renderCell(item: PurchaseOrderListItem, key: PurchaseOrderTableColumnKey) {
  switch (key) {
    case "order_number":
      return item.order_number || "—";
    case "order_item":
      return item.order_item || "—";
    case "product":
      return formatProductLabel(item.product_code, item.product_description);
    case "supplier":
      return item.supplier_name || item.supplier_code || "—";
    case "open_quantity":
      return item.open_quantity ?? "—";
    case "delivery":
      return formatDatePtBr(item.expected_delivery_date);
    case "status":
      return (
        <SuppliesStatusBadge
          label={labelDeliveryStatus(item.delivery_status)}
          variant={statusBadgeVariant(item.delivery_status)}
        />
      );
    case "open_value":
      return formatMoneyBr(item.open_value);
    default:
      return "—";
  }
}

export function PurchaseOrdersListTable({
  items,
  query,
  total,
  loading,
  onPatchQuery,
  onSelectRow,
}: PurchaseOrdersListTableProps) {
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
      .map((column) => ({
        key: column.key,
        header: column.label,
        sortable: false,
        render: (row: PurchaseOrderListItem) =>
          renderCell(row, column.key as PurchaseOrderTableColumnKey),
      }));
  }, [columnPrefs.visibleKeys]);

  const totalPages = Math.max(1, Math.ceil(total / query.page_size) || 1);

  const tableStyle = useMemo(
    (): CSSProperties =>
      ({
        "--delpi-ui-table-font-size": `${fontSizePrefs.fontSize}px`,
      }) as CSSProperties,
    [fontSizePrefs.fontSize],
  );

  return (
    <>
      <SuppliesDataListToolbar
        actions={
          <>
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
            role: "link",
          })}
          loading={loading}
        />
      </div>

      <SuppliesCompactPagination
        page={query.page}
        pageSize={query.page_size}
        total={total}
        totalPages={totalPages}
        disabled={loading}
        pageSizeOptions={[25, 50, 100]}
        onPageChange={(page) => onPatchQuery({ page })}
        onPageSizeChange={(pageSize) => onPatchQuery({ page_size: pageSize, page: 1 })}
      />
    </>
  );
}
