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
  getRowClassName?: (row: T) => string | undefined;
  compact?: boolean;
};

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage = "Nenhum registro encontrado.",
  loading = false,
  onRowClick,
  getRowClassName,
  compact = false,
}: DataTableProps<T>) {
  const tableClass = [
    "ds-table",
    onRowClick ? "ds-table--clickable" : "",
    compact ? "ds-table--compact" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="ds-table-wrap">
      <table className={tableClass}>
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
              <td colSpan={columns.length} className="ds-table__empty">
                Carregando…
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="ds-table__empty">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row) => {
              const extraClass = getRowClassName?.(row);
              const rowClass = [
                onRowClick ? "ds-table__row--clickable" : "",
                extraClass ?? "",
              ]
                .filter(Boolean)
                .join(" ");

              return (
                <tr
                  key={rowKey(row)}
                  className={rowClass || undefined}
                  onClick={
                    onRowClick
                      ? () => {
                          onRowClick(row);
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
