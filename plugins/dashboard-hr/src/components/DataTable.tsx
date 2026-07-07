import type { ReactNode } from "react";

import { HelpTooltip } from "@delpi/plugin-ui";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  headerHint?: string;
  render: (row: T) => ReactNode;
  className?: string;
  sortable?: boolean;
  sortValue?: (row: T) => string | number | null | undefined;
  /** Rótulo exibido no modo cartão (mobile). */
  mobileLabel?: string;
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
    <span className="dh-table__header-label">
      <span className="dh-table__header-text">{column.header}</span>
      {column.headerHint ? (
        <HelpTooltip
          content={column.headerHint}
          ariaLabel={`Ajuda: ${column.header}`}
          className="dh-table__header-help"
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
    "dh-table",
    layout === "section" ? "dh-table--section" : "",
    isSortable ? "dh-table--sortable" : "",
    onRowClick ? "dh-table--clickable" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const wrapClass =
    layout === "section"
      ? "dh-table-wrap dh-table-wrap--section"
      : "dh-table-wrap dh-table-wrap--embedded";

  if (loading) {
    return (
      <div className={wrapClass}>
        <table className={tableClass}>
          <tbody>
            <tr>
              <td colSpan={columns.length} className="dh-table__empty">
                Carregando…
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
        <table className={tableClass}>
          <tbody>
            <tr>
              <td colSpan={columns.length} className="dh-table__empty">
                {emptyMessage}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className={wrapClass}>
      <table className={tableClass}>
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
                      className={`dh-table__sort-button${
                        isSorted ? " dh-table__sort-button--active" : ""
                      }`}
                      onClick={() => onSortChange(column.key)}
                      aria-label={`Ordenar por ${column.header}`}
                    >
                      {renderColumnHeader(column)}
                      <span className="dh-table__sort-indicator" aria-hidden="true">
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
          {rows.map((row) => {
            const rowClass = [
              getRowClassName?.(row),
              onRowClick ? "dh-table__row--clickable" : "",
            ]
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
