import type { ReactNode } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

export type SortDirection = "asc" | "desc";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
  /** Quando definido, a coluna fica ordenável pelo valor retornado. */
  sortAccessor?: (row: T) => string | number | null | undefined;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  emptyMessage?: string;
  loading?: boolean;
  sortKey?: string | null;
  sortDir?: SortDirection;
  onSort?: (key: string) => void;
};

function SortIndicator({ state }: { state: SortDirection | null }) {
  if (state === "asc") return <ArrowUp size={13} aria-hidden="true" />;
  if (state === "desc") return <ArrowDown size={13} aria-hidden="true" />;
  return <ArrowUpDown size={13} aria-hidden="true" className="kz-table__sort-idle" />;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage = "Nenhum registro encontrado.",
  loading = false,
  sortKey = null,
  sortDir = "asc",
  onSort,
}: DataTableProps<T>) {
  return (
    <div className="kz-table-wrap">
      <table className="kz-table">
        <thead>
          <tr>
            {columns.map((column) => {
              const sortable = Boolean(column.sortAccessor && onSort);
              const active = sortable && sortKey === column.key;
              const state = active ? sortDir : null;
              return (
                <th
                  key={column.key}
                  className={column.className}
                  aria-sort={
                    active ? (sortDir === "asc" ? "ascending" : "descending") : undefined
                  }
                >
                  {sortable ? (
                    <button
                      type="button"
                      className={`kz-table__sort${active ? " kz-table__sort--active" : ""}`}
                      onClick={() => onSort?.(column.key)}
                    >
                      <span>{column.header}</span>
                      <SortIndicator state={state} />
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
              <td colSpan={columns.length} className="kz-table__empty">
                Carregando…
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="kz-table__empty">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={rowKey(row)}>
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
