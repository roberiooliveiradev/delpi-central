import { useMemo, type CSSProperties } from "react";

import { buildPurchaseRequestDetailPath } from "../../app/pluginRoutes";
import {
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  HelpTooltip,
  ExcelExportButton,
  SuppliesCompactPagination,
  SuppliesDataCardsSortBar,
  SuppliesDataListToolbar,
  SuppliesDataTable,
  SuppliesEntityLink,
  SuppliesSegmentToggle,
  SuppliesSelectField,
  SuppliesStatusBadge,
  SuppliesTableColumnVisibilityMenu,
  SuppliesTableFontSizeControls,
  usePersistedViewLayout,
  useTableColumnVisibility,
  useTableFontSize,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { PurchaseRequestsCards } from "./PurchaseRequestsCards";
import { PURCHASE_REQUESTS_CONTENT as C } from "./content";
import {
  formatDatePtBr,
  formatProductLabel,
  formatRequestNumber,
  labelOverallStage,
  nextServerSort,
  PURCHASE_REQUESTS_SORTABLE_COLUMNS,
  tableSortKey,
  type PurchaseRequestSortableColumnKey,
} from "./query";
import { purchaseRequestsColumnHelp } from "./purchaseRequestsColumnHelp";
import {
  PURCHASE_REQUESTS_COLUMN_STORAGE_KEY,
  PURCHASE_REQUESTS_TABLE_COLUMNS,
  PURCHASE_REQUESTS_TABLE_EMPTY_FALLBACK_KEYS,
  PURCHASE_REQUESTS_TABLE_FONT_SIZE_STORAGE_KEY,
  PURCHASE_REQUESTS_VIEW_LAYOUT_STORAGE_KEY,
  type PurchaseRequestTableColumnKey,
} from "./purchaseRequestsTableConfig";
import type {
  OverallStage,
  PurchaseRequestListItem,
  PurchaseRequestsQuery,
  PurchaseRequestsSortDir,
} from "./types";
import { OVERALL_STAGE_VALUES } from "./types";

type PurchaseRequestsListTableProps = {
  items: PurchaseRequestListItem[];
  query: PurchaseRequestsQuery;
  total: number;
  loading: boolean;
  canExport: boolean;
  basePath: string;
  onExport: () => void;
  onPatchQuery: (patch: Partial<PurchaseRequestsQuery>) => void;
  onSelectRow: (item: PurchaseRequestListItem) => void;
};

const CARDS_SORT_OPTIONS = PURCHASE_REQUESTS_TABLE_COLUMNS.filter(
  (column) => column.key in PURCHASE_REQUESTS_SORTABLE_COLUMNS,
).map((column) => ({
  value: column.key,
  label: column.label,
}));

function stageBadgeVariant(
  stage: string | null | undefined,
): "neutral" | "info" | "success" | "warning" | "danger" {
  switch (stage) {
    case "awaiting_order":
    case "awaiting_receipt":
      return "warning";
    case "partially_ordered":
    case "ordered":
    case "partially_received":
      return "info";
    case "completed":
      return "success";
    case "residual_closed":
      return "neutral";
    default:
      return "neutral";
  }
}

function isKnownStage(stage: string | null | undefined): stage is OverallStage {
  return Boolean(stage && (OVERALL_STAGE_VALUES as readonly string[]).includes(stage));
}

function buildRequestDetailHref(
  basePath: string,
  item: PurchaseRequestListItem,
): string {
  return buildPurchaseRequestDetailPath(item.branch, item.request_number, basePath);
}

export function PurchaseRequestsListTable({
  items,
  query,
  total,
  loading,
  canExport,
  basePath,
  onExport,
  onPatchQuery,
  onSelectRow,
}: PurchaseRequestsListTableProps) {
  const { layout, setLayout } = usePersistedViewLayout({
    storageKey: PURCHASE_REQUESTS_VIEW_LAYOUT_STORAGE_KEY,
  });

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
      .map((column) => {
        const key = column.key as PurchaseRequestTableColumnKey;
        return {
          key: column.key,
          header: column.label,
          headerHint: purchaseRequestsColumnHelp(key),
          sortable: key in PURCHASE_REQUESTS_SORTABLE_COLUMNS,
          interactive: key === "request_number",
          rowClick: key === "request_number" ? ("stop" as const) : undefined,
          render: (row: PurchaseRequestListItem) => {
            switch (key) {
              case "request_number": {
                const label = formatRequestNumber(row.request_number);
                const href = buildRequestDetailHref(basePath, row);
                return (
                  <SuppliesEntityLink
                    href={href}
                    title={C.openScLinkTitle(label)}
                    className="sp-entity-link"
                    onNavigate={() => onSelectRow(row)}
                  >
                    {label}
                  </SuppliesEntityLink>
                );
              }
              case "request_item":
                return row.request_item || "—";
              case "product":
                return formatProductLabel(row.product_code, row.product_description);
              case "requester":
                return row.requester?.name || row.requester?.code || "—";
              case "cost_center":
                return row.cost_center?.code || row.cost_center_code || "—";
              case "opened":
                return formatDatePtBr(row.request_issue_date);
              case "stage": {
                const stage = row.derived?.overall_stage;
                const label = labelOverallStage(stage);
                if (!isKnownStage(stage)) return label;
                return (
                  <SuppliesStatusBadge
                    label={label}
                    variant={stageBadgeVariant(stage)}
                  />
                );
              }
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

  const showCards = layout === "cards";
  const detailHref = (item: PurchaseRequestListItem) =>
    buildRequestDetailHref(basePath, item);

  const cardsSortKey =
    (tableSortKey(query.sort_by) as PurchaseRequestSortableColumnKey | null) ??
    "opened";
  const cardsSortDir: PurchaseRequestsSortDir = query.sort_dir === "asc" ? "asc" : "desc";

  const patchCardsSort = (columnKey: string, dir: PurchaseRequestsSortDir) => {
    const sortBy =
      PURCHASE_REQUESTS_SORTABLE_COLUMNS[columnKey as PurchaseRequestSortableColumnKey];
    if (!sortBy) return;
    onPatchQuery({ sort_by: sortBy, sort_dir: dir, page: 1 });
  };

  return (
    <>
      <SuppliesDataListToolbar
        leading={
          <HelpTooltip
            content={SP_HELP.purchaseRequestsView}
            ariaLabel="Ajuda: modo Tabela ou Cards"
            wrap
            placement="bottom"
          >
            <SuppliesSegmentToggle
              ariaLabel={C.viewAriaLabel}
              idPrefix="purchase-requests-layout"
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
            content={SP_HELP.purchaseRequestsTableMeta}
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
            {canExport ? (
              <HelpTooltip
                content={SP_HELP.purchaseRequestsExport}
                ariaLabel="Ajuda: exportar Excel"
                wrap
                placement="bottom"
              >
                <ExcelExportButton
                  density="toolbar"
                  onExport={onExport}
                  disabled={loading || total === 0}
                  label={C.exportLabel}
                  exportingLabel={C.excelExporting}
                />
              </HelpTooltip>
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
        }
      />

      {showCards ? (
        <>
          <SuppliesDataCardsSortBar
            style={tableStyle}
            sortField={
              <SuppliesSelectField
                label={C.sortByLabel}
                hint={SP_HELP.purchaseRequestsSort}
                value={cardsSortKey}
                options={CARDS_SORT_OPTIONS}
                onChange={(value) => patchCardsSort(value, cardsSortDir)}
              />
            }
            direction={
              <HelpTooltip
                content={SP_HELP.purchaseRequestsSortDirection}
                ariaLabel="Ajuda: direção da ordenação"
                wrap
                placement="bottom"
              >
                <SuppliesSegmentToggle
                  ariaLabel={C.sortDirectionAriaLabel}
                  idPrefix="purchase-requests-sort-dir"
                  size="sm"
                  value={cardsSortDir}
                  onChange={(dir) => {
                    if (dir === "asc" || dir === "desc") {
                      patchCardsSort(cardsSortKey, dir);
                    }
                  }}
                  options={[
                    { value: "asc", label: C.sortAscLabel },
                    { value: "desc", label: C.sortDescLabel },
                  ]}
                />
              </HelpTooltip>
            }
          />
          <PurchaseRequestsCards
            items={items}
            detailHref={detailHref}
            onSelectRow={onSelectRow}
          />
        </>
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
              `${row.branch}-${row.request_number}-${row.request_item ?? ""}`
            }
            onRowClick={onSelectRow}
            getRowProps={(row) => ({
              "aria-label": `${C.detailTitle} ${formatRequestNumber(row.request_number)}`,
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
        pageSizeOptions={[25, 50, 100]}
        onPageChange={(page) => onPatchQuery({ page })}
        onPageSizeChange={(pageSize) => onPatchQuery({ page_size: pageSize, page: 1 })}
      />
    </>
  );
}
