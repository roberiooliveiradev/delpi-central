import type { DataTableColumn } from "./types";
import { HelpTooltip } from "@delpi/plugin-ui";
import "./DataTable.css";

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  loading?: boolean;
  emptyMessage?: string;
  getRowKey: (row: T, index: number) => string;
  getRowClassName?: (row: T) => string | undefined;
  onRowClick?: (row: T) => void;
  sortKey?: string | null;
  sortDirection?: "asc" | "desc";
  onSortChange?: (columnKey: string) => void;
};

export function DataTable<T>({
  columns,
  rows,
  loading = false,
  emptyMessage = "Nenhum registro encontrado.",
  getRowKey,
  getRowClassName,
  onRowClick,
  sortKey = null,
  sortDirection = "asc",
  onSortChange,
}: DataTableProps<T>) {
  const tableClass = onRowClick ? "dm-datatable__table dm-datatable__table--clickable" : "dm-datatable__table";

  return (
    <div className="dm-datatable">
      <div className="dm-datatable__scroll">
        <table className={tableClass}>
          <thead>
            <tr>
              {columns.map((column) => {
                const isSorted = sortKey === column.key;
                const sortClass = column.sortable ? "dm-datatable__col--sortable" : "";
                const headerClass = [column.className, sortClass].filter(Boolean).join(" ");

                return (
                  <th
                    key={column.key}
                    className={headerClass || undefined}
                    data-align={column.align}
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
                        className="dm-datatable__sort-button"
                        onClick={() => onSortChange(column.key)}
                        aria-label={`Ordenar por ${column.header}`}
                      >
                        <span className="dm-datatable__header-label">
                          <span>{column.header}</span>
                          {column.headerHint ? (
                            <HelpTooltip
                              content={column.headerHint}
                              ariaLabel={`Ajuda: ${column.header}`}
                            />
                          ) : null}
                        </span>
                        <span className="dm-datatable__sort-indicator" aria-hidden="true">
                          {isSorted ? (sortDirection === "asc" ? "↑" : "↓") : "↕"}
                        </span>
                      </button>
                    ) : (
                      <span className="dm-datatable__header-label">
                        {column.header}
                        {column.headerHint ? (
                          <HelpTooltip content={column.headerHint} ariaLabel={`Ajuda: ${column.header}`} />
                        ) : null}
                      </span>
                    )}
                  </th>
                );
              })}
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
              rows.map((row, index) => {
                const rowClass = [getRowClassName?.(row), onRowClick ? "is-clickable" : ""]
                  .filter(Boolean)
                  .join(" ");

                return (
                  <tr
                    key={getRowKey(row, index)}
                    className={rowClass || undefined}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
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
                    tabIndex={onRowClick ? 0 : undefined}
                    role={onRowClick ? "button" : undefined}
                  >
                    {columns.map((column) => (
                      <td
                        key={column.key}
                        className={column.className}
                        data-label={column.header}
                        data-align={column.align}
                        data-interactive={column.interactive ? "true" : undefined}
                        onClick={
                          column.interactive
                            ? (event) => {
                                event.stopPropagation();
                              }
                            : undefined
                        }
                      >
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
    </div>
  );
}
