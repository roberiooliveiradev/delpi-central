import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  headerHint?: string;
  render: (row: T) => ReactNode;
  className?: string;
  sortable?: boolean;
  sortValue?: (row: T) => string | number | null | undefined;
  mobileLabel?: string;
};

export type DataTableClassNames = {
  wrapSection: string;
  wrapEmbedded: string;
  table: string;
  empty: string;
  headerLabel: string;
  headerText: string;
  headerHelp: string;
  sortButton: string;
  sortButtonActive: string;
  sortIndicator: string;
  rowClickable: string;
};

export type DataTableLabels = {
  emptyMessage: string;
  loadingMessage: string;
  sortByAriaLabel: (header: string) => string;
  headerHelpAriaLabel: (header: string) => string;
};

export type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  emptyMessage?: string;
  loading?: boolean;
  onRowClick?: (row: T) => void;
  getRowClassName?: (row: T) => string | undefined;
  sortKey?: string | null;
  sortDirection?: "asc" | "desc";
  onSortChange?: (columnKey: string) => void;
  layout?: "section" | "embedded";
  classNames: DataTableClassNames;
  labels: DataTableLabels;
};

export function dataTableBemClasses(prefix: string): DataTableClassNames {
  const table = `${prefix}-table`;
  return {
    wrapSection: `${prefix}-table-wrap ${prefix}-table-wrap--section`,
    wrapEmbedded: `${prefix}-table-wrap ${prefix}-table-wrap--embedded`,
    table,
    empty: `${table}__empty`,
    headerLabel: `${table}__header-label`,
    headerText: `${table}__header-text`,
    headerHelp: `${table}__header-help`,
    sortButton: `${table}__sort-button`,
    sortButtonActive: `${table}__sort-button ${table}__sort-button--active`,
    sortIndicator: `${table}__sort-indicator`,
    rowClickable: `${table}__row--clickable`,
  };
}

function buildTableClassName(
  classNames: DataTableClassNames,
  layout: "section" | "embedded",
  isSortable: boolean,
  clickable: boolean,
): string {
  return [
    classNames.table,
    layout === "section" ? `${classNames.table}--section` : "",
    isSortable ? `${classNames.table}--sortable` : "",
    clickable ? `${classNames.table}--clickable` : "",
  ]
    .filter(Boolean)
    .join(" ");
}

function renderColumnHeader<T>(
  column: DataTableColumn<T>,
  classNames: DataTableClassNames,
  labels: DataTableLabels,
) {
  return (
    <span className={classNames.headerLabel}>
      <span className={classNames.headerText}>{column.header}</span>
      {column.headerHint ? (
        <HelpTooltip
          content={column.headerHint}
          ariaLabel={labels.headerHelpAriaLabel(column.header)}
          className={classNames.headerHelp}
        />
      ) : null}
    </span>
  );
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage,
  loading = false,
  onRowClick,
  getRowClassName,
  sortKey = null,
  sortDirection = "asc",
  onSortChange,
  layout = "embedded",
  classNames,
  labels,
}: DataTableProps<T>) {
  const isSortable = Boolean(onSortChange && columns.some((column) => column.sortable));
  const resolvedEmptyMessage = emptyMessage ?? labels.emptyMessage;
  const wrapClass = layout === "section" ? classNames.wrapSection : classNames.wrapEmbedded;
  const tableClassName = buildTableClassName(
    classNames,
    layout,
    isSortable,
    Boolean(onRowClick),
  );

  if (loading) {
    return (
      <div className={wrapClass}>
        <table className={tableClassName}>
          <tbody>
            <tr>
              <td colSpan={columns.length} className={classNames.empty}>
                {labels.loadingMessage}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className={wrapClass}>
        <table className={tableClassName}>
          <tbody>
            <tr>
              <td colSpan={columns.length} className={classNames.empty}>
                {resolvedEmptyMessage}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className={wrapClass}>
      <table className={tableClassName}>
        <thead>
          <tr>
            {columns.map((column) => {
              const isSorted = sortKey === column.key;

              return (
                <th
                  key={column.key}
                  scope="col"
                  className={column.className}
                  aria-sort={
                    column.sortable
                      ? isSorted
                        ? sortDirection === "asc"
                          ? "ascending"
                          : "descending"
                        : "none"
                      : undefined
                  }
                >
                  {column.sortable && onSortChange ? (
                    <button
                      type="button"
                      className={isSorted ? classNames.sortButtonActive : classNames.sortButton}
                      onClick={() => onSortChange(column.key)}
                      aria-label={labels.sortByAriaLabel(column.header)}
                    >
                      {renderColumnHeader(column, classNames, labels)}
                      <span className={classNames.sortIndicator} aria-hidden="true">
                        {isSorted ? (sortDirection === "asc" ? "↑" : "↓") : "↕"}
                      </span>
                    </button>
                  ) : (
                    renderColumnHeader(column, classNames, labels)
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const rowClass = [getRowClassName?.(row), onRowClick ? classNames.rowClickable : ""]
              .filter(Boolean)
              .join(" ");

            return (
              <tr
                key={rowKey(row)}
                className={rowClass || undefined}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                tabIndex={onRowClick ? 0 : undefined}
                onKeyDown={
                  onRowClick
                    ? (event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          onRowClick(row);
                        }
                      }
                    : undefined
                }
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={column.className}
                    data-label={column.mobileLabel ?? column.header}
                  >
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export type DashboardDataTableProps<T> = Omit<DataTableProps<T>, "classNames" | "labels">;
