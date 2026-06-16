import type { ReactNode } from "react";

export type AdminDataTableColumn<T> = {
  id: string;
  header: string;
  render: (row: T, index: number) => ReactNode;
  className?: string;
};

type AdminDataTableProps<T> = {
  title?: string;
  columns: AdminDataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  emptyMessage?: string;
  caption?: string;
  onRowClick?: (row: T, index: number) => void;
  footer?: ReactNode;
};

export function AdminDataTable<T>({
  title,
  columns,
  rows,
  rowKey,
  emptyMessage = "Sem registros na janela.",
  caption,
  onRowClick,
  footer,
}: AdminDataTableProps<T>) {
  return (
    <div className="mdc-admin-data-table">
      {title ? <h4>{title}</h4> : null}
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
                <tr
                  key={rowKey(row, index)}
                  className={onRowClick ? "mdc-admin-data-table__row--clickable" : undefined}
                  onClick={onRowClick ? () => onRowClick(row, index) : undefined}
                >
                  {columns.map((column) => (
                    <td
                      key={column.id}
                      className={column.className}
                      data-label={column.header}
                    >
                      {column.render(row, index)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {footer}
    </div>
  );
}
