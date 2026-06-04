import type { ReactNode } from "react";

export type AdminDataTableColumn<T> = {
  id: string;
  header: string;
  render: (row: T, index: number) => ReactNode;
  className?: string;
};

type AdminDataTableProps<T> = {
  title: string;
  columns: AdminDataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  emptyMessage?: string;
  caption?: string;
};

export function AdminDataTable<T>({
  title,
  columns,
  rows,
  rowKey,
  emptyMessage = "Sem registros na janela.",
  caption,
}: AdminDataTableProps<T>) {
  return (
    <div className="mdc-admin-data-table">
      <h4>{title}</h4>
      {!rows.length ? (
        <p className="mdc-chat-muted">{emptyMessage}</p>
      ) : (
        <div className="mdc-admin-data-table__wrap">
          <table>
            {caption ? <caption className="sr-only">{caption}</caption> : null}
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.id} className={column.className}>
                    {column.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={rowKey(row, index)}>
                  {columns.map((column) => (
                    <td key={column.id} className={column.className}>
                      {column.render(row, index)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
