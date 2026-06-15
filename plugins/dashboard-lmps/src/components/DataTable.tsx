import type { ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  headerHint?: string;
  render: (row: T) => ReactNode;
  className?: string;
  sortable?: boolean;
  sortValue?: (row: T) => string | number | null | undefined;
};

type DataTableProps<T> = {
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
};

function renderColumnHeader<T>(column: DataTableColumn<T>) {
  return (
    <span className="lmps-table__header-label">
      <span className="lmps-table__header-text">{column.header}</span>
      {column.headerHint ? (
        <HelpTooltip
          content={column.headerHint}
          ariaLabel={`Ajuda: ${column.header}`}
          fixed
          className="lmps-table__header-help"
        />
      ) : null}
    </span>
  );
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage = "Nenhum registro encontrado.",
  loading = false,
  onRowClick,
  getRowClassName,
  sortKey = null,
  sortDirection = "asc",
  onSortChange,
  layout = "embedded",
}: DataTableProps<T>) {
  const isSortable = Boolean(onSortChange && columns.some((column) => column.sortable));
  const tableClass = [
    "lmps-table",
    layout === "section" ? "lmps-table--section" : "",
    isSortable ? "lmps-table--sortable" : "",
    onRowClick ? "lmps-table--clickable" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const table = (
      <table className={tableClass}>
        <thead>
          <tr>
            {columns.map((column) => {
              const isSorted = sortKey === column.key;
              const headerClass = column.className || undefined;

              return (
                <th
                  key={column.key}
                  scope="col"
                  className={headerClass}
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
                      className={`lmps-table__sort-button${
                        isSorted ? " lmps-table__sort-button--active" : ""
                      }`}
                      onClick={() => onSortChange(column.key)}
                      aria-label={`Ordenar por ${column.header}`}
                    >
                      {renderColumnHeader(column)}
                      <span className="lmps-table__sort-indicator" aria-hidden="true">
                        {isSorted ? (sortDirection === "asc" ? "↑" : "↓") : "↕"}
                      </span>
                    </button>
                  ) : (
                    renderColumnHeader(column)
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="lmps-table__empty">
                Carregando…
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="lmps-table__empty">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr
                key={rowKey(row)}
                className={getRowClassName?.(row)}
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
                  <td key={column.key} className={column.className}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
  );

  const wrapClass =
    layout === "section"
      ? "lmps-table-wrap lmps-table-wrap--section"
      : "lmps-table-wrap lmps-table-wrap--embedded";

  return <div className={wrapClass}>{table}</div>;
}
