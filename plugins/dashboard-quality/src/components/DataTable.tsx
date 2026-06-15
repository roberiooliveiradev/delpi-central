import type { ReactNode } from "react";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  emptyMessage?: string;
  loading?: boolean;
  onRowClick?: (row: T) => void;
};

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage = "Nenhum registro encontrado.",
  loading = false,
  onRowClick,
}: DataTableProps<T>) {
  return (
    <div className="dq-table-wrap">
      <table className="dq-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={column.className}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="dq-table__empty">
                Carregando…
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="dq-table__empty">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row) => {
              const isClickable = Boolean(onRowClick);

              return (
                <tr
                  key={rowKey(row)}
                  className={isClickable ? "dq-row--clickable" : undefined}
                  tabIndex={isClickable ? 0 : undefined}
                  onClick={isClickable ? () => onRowClick?.(row) : undefined}
                  onKeyDown={
                    isClickable
                      ? (event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            onRowClick?.(row);
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
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
