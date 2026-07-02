import type { ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  sortable?: boolean;
  sortValue?: (row: T) => string | number | boolean | null | undefined;
  className?: string;
  /** Texto do balão explicativo exibido ao lado do cabeçalho da coluna. */
  headerHint?: string;
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
  compact = false,
  sortKey,
  sortDirection = "asc",
  onSortChange,
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
            {columns.map((column) => {
              const isSorted = sortKey === column.key;
              const sortClass = column.sortable ? "ds-table__col--sortable" : "";
              const headerClass = [column.className, sortClass].filter(Boolean).join(" ");

              return (
                <th
                  key={column.key}
                  className={headerClass || undefined}
                  aria-sort={column.sortable ? (isSorted ? (sortDirection === "asc" ? "ascending" : "descending") : "none") : undefined}
                >
                  {column.sortable && onSortChange ? (
                    <span className="ds-table__header-cell">
                      <button
                        type="button"
                        className="ds-table__sort-button"
                        onClick={() => onSortChange(column.key)}
                        aria-label={`Ordenar por ${column.header}`}
                      >
                        <span>{column.header}</span>
                        <span className="ds-table__sort-indicator">
                          {isSorted ? (sortDirection === "asc" ? "↑" : "↓") : "↕"}
                        </span>
                      </button>
                      {column.headerHint ? (
                        <HelpTooltip
                          content={column.headerHint}
                          ariaLabel={`Ajuda: ${column.header}`}
                        />
                      ) : null}
                    </span>
                  ) : column.headerHint ? (
                    <span className="ds-table__header-cell">
                      {column.header}
                      <HelpTooltip
                        content={column.headerHint}
                        ariaLabel={`Ajuda: ${column.header}`}
                      />
                    </span>
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
