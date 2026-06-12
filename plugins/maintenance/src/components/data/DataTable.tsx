import type { DataTableColumn } from "./types";
import "./DataTable.css";

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  loading?: boolean;
  emptyMessage?: string;
  getRowKey: (row: T, index: number) => string;
  getRowClassName?: (row: T) => string | undefined;
};

export function DataTable<T>({
  columns,
  rows,
  loading = false,
  emptyMessage = "Nenhum registro encontrado.",
  getRowKey,
  getRowClassName,
}: DataTableProps<T>) {
  return (
    <div className="dm-datatable">
      <div className="dm-datatable__scroll">
        <table className="dm-datatable__table">
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
                <td colSpan={columns.length}>
                  <div className="dm-datatable__empty">Carregando…</div>
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>
                  <div className="dm-datatable__empty">{emptyMessage}</div>
                </td>
              </tr>
            ) : (
              rows.map((row, index) => (
                <tr key={getRowKey(row, index)} className={getRowClassName?.(row)}>
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={column.className}
                      data-label={column.header}
                      data-align={column.align}
                    >
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
