import type { ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  headerHint?: string;
  render: (row: T) => ReactNode;
  className?: string;
  sortable?: boolean;
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
};

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
}: DataTableProps<T>) {
  const tableClass = onRowClick
    ? "dp-table dp-table--clickable"
    : "dp-table";

  return (
    <div className="dp-table-wrap">
      <table className={tableClass}>
        <thead>
          <tr>
            {columns.map((column) => {
              const isSorted = sortKey === column.key;
              const headerClass = [
                column.className,
                column.sortable ? "dp-table__col--sortable" : "",
              ]
                .filter(Boolean)
                .join(" ");

              return (
                <th
                  key={column.key}
                  className={headerClass || undefined}
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
                      className="dp-table__sort-button"
                      onClick={() => onSortChange(column.key)}
                      aria-label={`Ordenar por ${column.header}`}
                    >
                      <span className="dp-table__header-label">
                        <span>{column.header}</span>
                        {column.headerHint ? (
                          <HelpTooltip
                            content={column.headerHint}
                            ariaLabel={`Ajuda: ${column.header}`}
                          />
                        ) : null}
                      </span>
                      <span className="dp-table__sort-indicator" aria-hidden="true">
                        {isSorted ? (sortDirection === "asc" ? "↑" : "↓") : "↕"}
                      </span>
                    </button>
                  ) : (
                    <span className="dp-table__header-label">
                      {column.header}
                      {column.headerHint ? (
                        <HelpTooltip
                          content={column.headerHint}
                          ariaLabel={`Ajuda: ${column.header}`}
                        />
                      ) : null}
                    </span>
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="dp-table__empty">
                Carregando…
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="dp-table__empty">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row) => {
              const extraClass = getRowClassName?.(row);
              const rowClass = [extraClass, onRowClick ? "is-clickable" : ""]
                .filter(Boolean)
                .join(" ");

              return (
                <tr
                  key={rowKey(row)}
                  className={rowClass || undefined}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
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
                  tabIndex={onRowClick ? 0 : undefined}
                  role={onRowClick ? "button" : undefined}
                >
                  {columns.map((column) => (
                    <td key={column.key} className={column.className}>
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
