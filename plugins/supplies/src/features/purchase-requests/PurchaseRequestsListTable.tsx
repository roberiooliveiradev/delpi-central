import { Download } from "lucide-react";
import { useMemo, type CSSProperties, type ReactNode } from "react";

import {
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  SuppliesActionButton,
  SuppliesCompactPagination,
  SuppliesDataListToolbar,
  SuppliesDataTable,
  SuppliesTableColumnVisibilityMenu,
  SuppliesTableFontSizeControls,
  useTableColumnVisibility,
  useTableFontSize,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { PURCHASE_REQUESTS_CONTENT as C } from "./content";
import {
  buildRequestKey,
  formatDatePtBr,
  formatProductLabel,
  formatRequestNumber,
  labelOverallStage,
} from "./query";
import {
  PURCHASE_REQUESTS_COLUMN_STORAGE_KEY,
  PURCHASE_REQUESTS_TABLE_COLUMNS,
  PURCHASE_REQUESTS_TABLE_EMPTY_FALLBACK_KEYS,
  PURCHASE_REQUESTS_TABLE_FONT_SIZE_STORAGE_KEY,
  type PurchaseRequestTableColumnKey,
} from "./purchaseRequestsTableConfig";
import type { PurchaseRequestListItem, PurchaseRequestsQuery } from "./types";

type PurchaseRequestsListTableProps = {
  items: PurchaseRequestListItem[];
  query: PurchaseRequestsQuery;
  total: number;
  loading: boolean;
  canExport: boolean;
  onExport: () => void;
  onPatchQuery: (patch: Partial<PurchaseRequestsQuery>) => void;
  onSelectRow: (item: PurchaseRequestListItem) => void;
};

function renderCell(item: PurchaseRequestListItem, key: PurchaseRequestTableColumnKey) {
  switch (key) {
    case "request_number":
      return formatRequestNumber(item.request_number);
    case "request_item":
      return item.request_item || "—";
    case "product":
      return formatProductLabel(item.product_code, item.product_description);
    case "requester":
      return item.requester?.name || item.requester?.code || "—";
    case "cost_center":
      return item.cost_center?.code || item.cost_center_code || "—";
    case "opened":
      return formatDatePtBr(item.request_issue_date);
    case "stage":
      return labelOverallStage(item.derived?.overall_stage);
    default:
      return "—";
  }
}

export function PurchaseRequestsListTable({
  items,
  query,
  total,
  loading,
  canExport,
  onExport,
  onPatchQuery,
  onSelectRow,
}: PurchaseRequestsListTableProps) {
  const columnPrefs = useTableColumnVisibility({
    storageKey: PURCHASE_REQUESTS_COLUMN_STORAGE_KEY,
    columns: PURCHASE_REQUESTS_TABLE_COLUMNS,
    emptyFallbackKeys: PURCHASE_REQUESTS_TABLE_EMPTY_FALLBACK_KEYS,
  });

  const fontSizePrefs = useTableFontSize({
    storageKey: PURCHASE_REQUESTS_TABLE_FONT_SIZE_STORAGE_KEY,
  });

  const columns = useMemo((): DataTableColumn<PurchaseRequestListItem>[] => {
    const byKey = new Map(
      PURCHASE_REQUESTS_TABLE_COLUMNS.map((column) => [column.key, column]),
    );
    return columnPrefs.visibleKeys
      .map((key) => byKey.get(key as PurchaseRequestTableColumnKey))
      .filter((column): column is (typeof PURCHASE_REQUESTS_TABLE_COLUMNS)[number] =>
        Boolean(column),
      )
      .map((column) => ({
        key: column.key,
        header: column.label,
        sortable: false,
        render: (row: PurchaseRequestListItem) =>
          renderCell(row, column.key as PurchaseRequestTableColumnKey),
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

  const toolbarActions: ReactNode = (
    <>
      {canExport ? (
        <SuppliesActionButton
          type="button"
          variant="ghost"
          title={C.exportTitle}
          onClick={onExport}
          disabled={loading}
        >
          <Download size={16} strokeWidth={1.75} aria-hidden="true" />{" "}
          {C.exportLabel}
        </SuppliesActionButton>
      ) : null}
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
  );

  return (
    <>
      <SuppliesDataListToolbar actions={toolbarActions} />

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
            `${row.branch}-${row.request_number}-${row.request_item ?? ""}`
          }
          onRowClick={onSelectRow}
          getRowClassName={(row) =>
            query.request === buildRequestKey(row.branch, row.request_number)
              ? "is-selected"
              : undefined
          }
          getRowProps={(row) => ({
            "aria-label": `${C.detailTitle} ${formatRequestNumber(row.request_number)}`,
            role: "button",
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
