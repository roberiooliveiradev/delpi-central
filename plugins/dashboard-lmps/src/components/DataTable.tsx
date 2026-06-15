import type { ReactNode } from "react";

export type DataTableColumn<T> = {
  key: string;
  header: string;
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
  const tableClass = onRowClick ? "lmps-table lmps-table--clickable" : "lmps-table";

  return (
    <div className="lmps-table-wrapper">
      <table className={tableClass}>
        <thead>
          <tr>
            {columns.map((column) => {
              const isSorted = sortKey === column.key;
              const headerClass = [
                column.className,
                column.sortable ? "lmps-table__col--sortable" : "",
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
                      className="lmps-table__sort-button"
                      onClick={() => onSortChange(column.key)}
                      aria-label={`Ordenar por ${column.header}`}
                    >
                      <span>{column.header}</span>
                      <span className="lmps-table__sort-indicator" aria-hidden="true">
                        {isSorted ? (sortDirection === "asc" ? "↑" : "↓") : "↕"}
                      </span>
                    </button>
                  ) : (
                    column.header
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
    </div>
  );
}
