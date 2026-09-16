import { useMemo, type CSSProperties } from "react";

import { buildPurchaseOrderDetailPath } from "../../app/pluginRoutes";
import {
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  HelpTooltip,
  SuppliesCompactPagination,
  SuppliesDataListToolbar,
  SuppliesDataTable,
  SuppliesEntityLink,
  SuppliesStatusBadge,
  SuppliesTableColumnVisibilityMenu,
  SuppliesTableFontSizeControls,
  spDataTableClassNames,
  useTableColumnVisibility,
  useTableFontSize,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { PURCHASE_ORDERS_CONTENT as C } from "./content";
import {
  formatDatePtBr,
  formatMoneyBr,
  formatProductLabel,
  labelDeliveryStatus,
} from "./query";
import { purchaseOrdersColumnHelp } from "./purchaseOrdersColumnHelp";
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
          sortable: false,
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

  return (
    <>
      <SuppliesDataListToolbar
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
