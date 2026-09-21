import { useMemo, type CSSProperties } from "react";

import { SuppliesSupplierIdentity } from "../../app/SuppliesDirectoryIdentity";
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
import { DELIVERIES_CONTENT as C } from "./content";
import {
  DELIVERIES_COLUMN_STORAGE_KEY,
  DELIVERIES_TABLE_COLUMNS,
  DELIVERIES_TABLE_EMPTY_FALLBACK_KEYS,
  DELIVERIES_TABLE_FONT_SIZE_STORAGE_KEY,
  type DeliveryTableColumnKey,
} from "./deliveriesTableConfig";
import {
  formatDatePtBr,
  formatDaysDiff,
  formatProductLabel,
  formatQuantity,
  labelDeliveryStatus,
  nextServerSort,
  tableSortKey,
} from "./query";
import type { DeliveriesQuery, DeliveryLateListItem } from "./types";
import { DELIVERIES_PAGE_SIZE_OPTIONS } from "./types";

type DeliveriesListTableProps = {
  items: DeliveryLateListItem[];
  query: DeliveriesQuery;
  total: number;
  totalPages: number;
  loading: boolean;
  onPatchQuery: (patch: Partial<DeliveriesQuery>) => void;
};

function statusBadgeVariant(
  status: string | null | undefined,
): "danger" | "success" | "neutral" {
  if (status === "late") return "danger";
  if (status === "on_time") return "success";
  return "neutral";
}

export function DeliveriesListTable({
  items,
  query,
  total,
  totalPages,
  loading,
  onPatchQuery,
}: DeliveriesListTableProps) {
  const columnPrefs = useTableColumnVisibility({
    storageKey: DELIVERIES_COLUMN_STORAGE_KEY,
    columns: DELIVERIES_TABLE_COLUMNS,
    emptyFallbackKeys: DELIVERIES_TABLE_EMPTY_FALLBACK_KEYS,
  });

  const fontSizePrefs = useTableFontSize({
    storageKey: DELIVERIES_TABLE_FONT_SIZE_STORAGE_KEY,
  });

  const columns = useMemo((): DataTableColumn<DeliveryLateListItem>[] => {
    const byKey = new Map(
      DELIVERIES_TABLE_COLUMNS.map((column) => [column.key, column]),
    );
    return columnPrefs.visibleKeys
      .map((key) => byKey.get(key as DeliveryTableColumnKey))
      .filter((column): column is (typeof DELIVERIES_TABLE_COLUMNS)[number] =>
        Boolean(column),
      )
      .map((column) => {
        const key = column.key as DeliveryTableColumnKey;
        const numeric =
          key === "quantity" || key === "days_diff"
            ? {
                align: "right" as const,
                className: spDataTableClassNames.colNumeric,
              }
            : {};
        return {
          key: column.key,
          header: column.label,
          sortable: true,
          ...numeric,
          render: (row: DeliveryLateListItem) => {
            switch (key) {
              case "branch":
                return formatSuppliesUnitName(row.branch);
              case "order_number":
                return row.order_number || "—";
              case "order_item":
                return row.order_item || "—";
              case "product":
                return formatProductLabel(row.product_code, row.product_description);
              case "supplier":
                return (
                  <SuppliesSupplierIdentity
                    name={row.supplier_name || row.supplier_short_name}
                    code={row.supplier_code}
                    store={row.supplier_store}
                  />
                );
              case "quantity":
                return formatQuantity(row.quantity);
              case "expected_delivery_date":
                return formatDatePtBr(row.expected_delivery_date);
              case "receipt_entry_date":
                return formatDatePtBr(row.receipt_entry_date);
              case "days_diff":
                return formatDaysDiff(row.days_diff);
              case "status":
                return (
                  <SuppliesStatusBadge
                    label={labelDeliveryStatus(row.status)}
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
            content={SP_HELP.deliveriesTableMeta}
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
            `${row.branch}-${row.order_number}-${row.order_item ?? ""}-${row.receipt_entry_date ?? ""}-${row.days_diff ?? ""}`
          }
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

      <SuppliesCompactPagination
        page={query.page}
        pageSize={query.page_size}
        total={total}
        totalPages={Math.max(1, totalPages || 1)}
        disabled={loading}
        pageSizeOptions={[...DELIVERIES_PAGE_SIZE_OPTIONS]}
        onPageChange={(page) => onPatchQuery({ page })}
        onPageSizeChange={(pageSize) => onPatchQuery({ page_size: pageSize, page: 1 })}
      />
    </>
  );
}
