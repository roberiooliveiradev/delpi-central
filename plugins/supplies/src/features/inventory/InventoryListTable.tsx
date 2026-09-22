import { useMemo, type CSSProperties } from "react";

import { formatSuppliesUnitName } from "../../app/suppliesUnits";
import {
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  HelpTooltip,
  SuppliesCompactPagination,
  SuppliesDataListToolbar,
  SuppliesDataTable,
  SuppliesTableColumnVisibilityMenu,
  SuppliesTableFontSizeControls,
  spDataTableClassNames,
  useTableColumnVisibility,
  useTableFontSize,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { INVENTORY_CONTENT as C } from "./content";
import {
  INVENTORY_COLUMN_STORAGE_KEY,
  INVENTORY_TABLE_COLUMNS,
  INVENTORY_TABLE_EMPTY_FALLBACK_KEYS,
  INVENTORY_TABLE_FONT_SIZE_STORAGE_KEY,
  type InventoryTableColumnKey,
} from "./inventoryTableConfig";
import {
  formatMoneyBr,
  formatQuantity,
  formatUnitOfMeasure,
  formatWarehouseDisplay,
  nextServerSort,
  tableSortDirection,
  tableSortKey,
} from "./query";
import type { InventoryQuery, InventoryStockItem } from "./types";
import { INVENTORY_PAGE_SIZE_OPTIONS } from "./types";

type InventoryListTableProps = {
  items: InventoryStockItem[];
  query: InventoryQuery;
  total: number;
  totalPages: number;
  loading: boolean;
  onPatchQuery: (patch: Partial<InventoryQuery>) => void;
};

export function InventoryListTable({
  items,
  query,
  total,
  totalPages,
  loading,
  onPatchQuery,
}: InventoryListTableProps) {
  const columnPrefs = useTableColumnVisibility({
    storageKey: INVENTORY_COLUMN_STORAGE_KEY,
    columns: INVENTORY_TABLE_COLUMNS,
    emptyFallbackKeys: INVENTORY_TABLE_EMPTY_FALLBACK_KEYS,
  });

  const fontSizePrefs = useTableFontSize({
    storageKey: INVENTORY_TABLE_FONT_SIZE_STORAGE_KEY,
  });

  const columns = useMemo((): DataTableColumn<InventoryStockItem>[] => {
    const byKey = new Map(
      INVENTORY_TABLE_COLUMNS.map((column) => [column.key, column]),
    );
    return columnPrefs.visibleKeys
      .map((key) => byKey.get(key as InventoryTableColumnKey))
      .filter((column): column is (typeof INVENTORY_TABLE_COLUMNS)[number] =>
        Boolean(column),
      )
      .map((column) => {
        const key = column.key as InventoryTableColumnKey;
        const numeric =
          key === "quantity" || key === "unit_cost" || key === "stock_value"
            ? {
                align: "right" as const,
                className: spDataTableClassNames.colNumeric,
              }
            : {};
        const sortable =
          key === "product_code" || key === "quantity" || key === "stock_value";
        return {
          key: column.key,
          header: column.label,
          sortable,
          ...numeric,
          render: (row: InventoryStockItem) => {
            switch (key) {
              case "product_code":
                return row.product_code?.trim() || "—";
              case "description":
                return row.description?.trim() || "—";
              case "unit_of_measure":
                return formatUnitOfMeasure(row.unit_of_measure);
              case "branch":
                return formatSuppliesUnitName(row.branch);
              case "warehouse":
                return formatWarehouseDisplay(row.warehouse, row.warehouse_label);
              case "quantity":
                return (
                  <span title={SP_HELP.inventoryPhysicalBalance}>
                    {formatQuantity(row.quantity)}
                  </span>
                );
              case "unit_cost":
                return formatMoneyBr(row.unit_cost);
              case "stock_value":
                return (
                  <span title={SP_HELP.inventoryStockValue}>
                    {formatMoneyBr(row.stock_value)}
                  </span>
                );
              default:
                return "—";
            }
          },
        };
      });
  }, [columnPrefs.visibleKeys]);

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
            content={SP_HELP.inventoryTableMeta}
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
          rowKey={(row, index) =>
            `${row.branch ?? ""}|${row.warehouse ?? ""}|${row.product_code ?? ""}|${index}`
          }
          loading={loading}
          sortKey={tableSortKey(query.sort)}
          sortDirection={tableSortDirection(query.sort)}
          onSortChange={(columnKey) => {
            const next = nextServerSort(query, columnKey);
            if (next) onPatchQuery(next);
          }}
          enableColumnReorder
          onColumnOrderChange={columnPrefs.applyVisibleOrder}
        />
      </div>

      <SuppliesCompactPagination
        page={query.page}
        pageSize={query.page_size}
        total={total}
        totalPages={Math.max(1, totalPages || 1)}
        disabled={loading}
        pageSizeOptions={[...INVENTORY_PAGE_SIZE_OPTIONS]}
        onPageChange={(page) => onPatchQuery({ page })}
        onPageSizeChange={(pageSize) => onPatchQuery({ page_size: pageSize, page: 1 })}
      />
    </>
  );
}
