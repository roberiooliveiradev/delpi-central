import type { ReactNode } from "react";
import "./DataTable.css";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render?: (row: T) => ReactNode;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  loading?: boolean;
  emptyText?: string;
  getRowKey: (row: T, index: number) => string;
};

export function DataTable<T>({
  columns,
  rows,
  loading = false,
  emptyText = "Nenhum registro encontrado.",
  getRowKey,
}: DataTableProps<T>) {
  return (
    <div className="si-datatable">
      <div className="si-datatable__container">
        <table className="si-datatable__table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key}>{column.header}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length}>
                  <div className="si-datatable__state">Carregando...</div>
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>
                  <div className="si-datatable__state">{emptyText}</div>
                </td>
              </tr>
            ) : (
              rows.map((row, index) => (
                <tr key={getRowKey(row, index)}>
                  {columns.map((column) => (
                    <td key={column.key} data-label={column.header}>
                      {column.render ? column.render(row) : "-"}
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