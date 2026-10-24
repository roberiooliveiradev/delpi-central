import { useMemo, type CSSProperties } from "react";

import { formatSuppliesUnitName } from "../../app/suppliesUnits";
import {
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  HelpTooltip,
  SuppliesCompactPagination,
  SuppliesDataListToolbar,
  SuppliesDataTable,
  SuppliesStatusBadge,
  SuppliesTableColumnVisibilityMenu,
  SuppliesTableFontSizeControls,
  spDataTableClassNames,
  useTableColumnVisibility,
  useTableFontSize,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import {
  SAFETY_STOCK_CONTENT as C,
  labelSafetyStockStatus,
  statusBadgeVariant,
} from "./content";
import {
  formatQuantity,
  formatUnitOfMeasure,
  nextServerSort,
} from "./query";
import {
  SAFETY_STOCK_COLUMN_STORAGE_KEY,
  SAFETY_STOCK_SORTABLE_COLUMNS,
  SAFETY_STOCK_TABLE_COLUMNS,
  SAFETY_STOCK_TABLE_EMPTY_FALLBACK_KEYS,
  SAFETY_STOCK_TABLE_FONT_SIZE_STORAGE_KEY,
  safetyStockRowKey,
  type SafetyStockTableColumnKey,
} from "./safetyStockTableConfig";
import type { SafetyStockItem, SafetyStockQuery } from "./types";
import { SAFETY_STOCK_PAGE_SIZE_OPTIONS } from "./types";

const NUMERIC_COLUMNS = new Set<SafetyStockTableColumnKey>([
  "safety_stock",
  "primary_stock",
  "work_in_process_stock",
  "deficit_quantity",
]);

type SafetyStockListTableProps = {
  items: SafetyStockItem[];
  query: SafetyStockQuery;
  total: number;
  totalPages: number;
  loading: boolean;
  onPatchQuery: (patch: Partial<SafetyStockQuery>) => void;
};

export function SafetyStockListTable({
  items,
  query,
  total,
  totalPages,
  loading,
  onPatchQuery,
}: SafetyStockListTableProps) {
  const columnPrefs = useTableColumnVisibility({
    storageKey: SAFETY_STOCK_COLUMN_STORAGE_KEY,
    columns: SAFETY_STOCK_TABLE_COLUMNS,
    emptyFallbackKeys: SAFETY_STOCK_TABLE_EMPTY_FALLBACK_KEYS,
  });

  const fontSizePrefs = useTableFontSize({
    storageKey: SAFETY_STOCK_TABLE_FONT_SIZE_STORAGE_KEY,
  });

  const columns = useMemo((): DataTableColumn<SafetyStockItem>[] => {
    const byKey = new Map(
      SAFETY_STOCK_TABLE_COLUMNS.map((column) => [column.key, column]),
    );
    return columnPrefs.visibleKeys
      .map((key) => byKey.get(key as SafetyStockTableColumnKey))
      .filter((column): column is (typeof SAFETY_STOCK_TABLE_COLUMNS)[number] =>
        Boolean(column),
      )
      .map((column) => {
        const key = column.key as SafetyStockTableColumnKey;
        const numeric = NUMERIC_COLUMNS.has(key)
          ? {
              align: "right" as const,
              className: spDataTableClassNames.colNumeric,
            }
          : {};
        return {
          key: column.key,
          header: column.label,
          sortable: SAFETY_STOCK_SORTABLE_COLUMNS.has(key),
          ...numeric,
          render: (row: SafetyStockItem) => {
            switch (key) {
              case "product_code":
                return row.product_code?.trim() || "—";
              case "product_description":
                return (
                  <span>
                    {row.product_description?.trim() || "—"}
                    {row.blocked ? (
                      <>
                        {" "}
                        <SuppliesStatusBadge label="Bloqueado" variant="neutral" />
                      </>
                    ) : null}
                  </span>
                );
              case "branch":
                return formatSuppliesUnitName(row.branch);
              case "product_type":
                return row.product_type?.trim() || "—";
              case "product_group":
                return row.product_group?.trim() || "—";
              case "unit":
                return formatUnitOfMeasure(row.unit);
              case "safety_stock":
                return (
                  <span title={SP_HELP.safetyStockSafetyStock}>
                    {formatQuantity(row.safety_stock)}
                  </span>
                );
              case "primary_stock":
                return (
                  <span title={SP_HELP.safetyStockPrimaryStock}>
                    {formatQuantity(row.primary_stock)}
                  </span>
                );
              case "work_in_process_stock":
                return (
                  <span title={SP_HELP.safetyStockWorkInProcess}>
                    {formatQuantity(row.work_in_process_stock)}
                  </span>
                );
              case "deficit_quantity":
                return (
                  <span title={SP_HELP.safetyStockDeficit}>
                    {formatQuantity(row.deficit_quantity)}
                  </span>
                );
              case "status":
                return (
                  <SuppliesStatusBadge
                    label={labelSafetyStockStatus(row.status)}
                    variant={statusBadgeVariant(row.status)}
                  />
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
            content={SP_HELP.safetyStockTableMeta}
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
            safetyStockRowKey(row.product_code, row.branch, index)
          }
          loading={loading}
          sortKey={query.sortBy}
          sortDirection={query.sortDirection}
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
        pageSizeOptions={[...SAFETY_STOCK_PAGE_SIZE_OPTIONS]}
        onPageChange={(page) => onPatchQuery({ page })}
        onPageSizeChange={(pageSize) =>
          onPatchQuery({ page_size: pageSize, page: 1 })
        }
      />
    </>
  );
}
