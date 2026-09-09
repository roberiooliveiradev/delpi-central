import type { ReactNode } from "react";
import { HelpTooltip, delpiUiClass } from "@delpi/plugin-ui/index";

export type AdminDataTableColumn<T> = {
  id: string;
  header: string;
  headerHint?: string;
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

/**
 * Tabela admin — dual-class com `delpi-ui-table` / wrap do kit (convergência gradual).
 */
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
    <div className={delpiUiClass("mdc-admin-data-table", "delpi-ui-table-section")}>
      {title ? (
        <h4 className={delpiUiClass("mdc-admin-data-table__title", "delpi-ui-section-title")}>
          {title}
        </h4>
      ) : null}
      {!rows.length ? (
        <p className="mdc-chat-muted">{emptyMessage}</p>
      ) : (
        <div className={delpiUiClass("mdc-admin-data-table__wrap", "delpi-ui-table-wrap")}>
          <table className={delpiUiClass("mdc-admin-data-table__table", "delpi-ui-table")}>
            {caption ? <caption className="sr-only">{caption}</caption> : null}
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.id} className={column.className}>
                    {column.headerHint ? (
                      <HelpTooltip
                        content={column.headerHint}
                        ariaLabel={`Ajuda: ${column.header}`}
                        wrap
                        placement="bottom"
                      >
                        <span>{column.header}</span>
                      </HelpTooltip>
                    ) : (
                      column.header
                    )}
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
