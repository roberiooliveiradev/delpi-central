// src/components/DataTable.tsx

import { useMemo } from "react";
import type { ReactNode } from "react";
import { ArrowUpDown, ChevronLeft, ChevronRight, Search } from "lucide-react";
import "./DataTable.css";

export type DataTableColumn<T> = {
  key: keyof T | string;
  header: string;
  sortable?: boolean;
  width?: number | string;
  render?: (row: T) => ReactNode;
};

export type DataTableSort = {
  sort?: string;
  direction?: "asc" | "desc";
};

export type DataTablePagination = {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
};

export type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  data: T[];
  loading?: boolean;

  // Search (controlled)
  searchValue?: string;
  onSearchChange?: (value: string) => void;

  // Toolbar slot
  toolbar?: ReactNode;

  // Sorting (server-side)
  sort?: DataTableSort;
  onSortChange?: (next: DataTableSort) => void;

  // Pagination (server-side)
  pagination?: DataTablePagination;
  onPageChange?: (page: number) => void;

  // Page size selector
  pageSizeOptions?: number[];
  onPageSizeChange?: (pageSize: number) => void;

  // Row actions
  actions?: (row: T) => ReactNode;

  // Bulk selection
  selectable?: boolean;
  getRowId?: (row: T) => string;
  selectedRows?: string[];
  onSelectionChange?: (ids: string[]) => void;

  emptyText?: string;
};

export function DataTable<T>({
  columns,
  data,
  loading,
  searchValue,
  onSearchChange,
  toolbar,
  sort,
  onSortChange,
  pagination,
  onPageChange,
  pageSizeOptions = [10, 20, 50, 100],
  onPageSizeChange,
  actions,
  selectable,
  getRowId,
  selectedRows = [],
  onSelectionChange,
  emptyText = "Nenhum registro encontrado.",
}: DataTableProps<T>) {
  const hasSearch = typeof onSearchChange === "function";
  const hasPagination = !!pagination && typeof onPageChange === "function";
  const hasPageSize = typeof onPageSizeChange === "function" && !!pagination;
  const hasSort = typeof onSortChange === "function";

  const rows = data ?? [];

  const allSelected = useMemo(() => {
    if (!selectable || !getRowId || rows.length === 0) return false;
    return rows.every((r) => selectedRows.includes(getRowId(r)));
  }, [rows, selectable, getRowId, selectedRows]);

  const toggleAll = () => {
    if (!selectable || !getRowId || !onSelectionChange) return;

    if (allSelected) {
      const remaining = selectedRows.filter(
        (id) => !rows.some((r) => getRowId(r) === id)
      );
      onSelectionChange(remaining);
      return;
    }

    const toAdd = rows.map((r) => getRowId(r));
    const merged = Array.from(new Set([...selectedRows, ...toAdd]));
    onSelectionChange(merged);
  };

  const toggleRow = (row: T) => {
    if (!selectable || !getRowId || !onSelectionChange) return;

    const id = getRowId(row);
    if (selectedRows.includes(id)) {
      onSelectionChange(selectedRows.filter((x) => x !== id));
    } else {
      onSelectionChange([...selectedRows, id]);
    }
  };

  const isSelected = (row: T) => {
    if (!selectable || !getRowId) return false;
    return selectedRows.includes(getRowId(row));
  };

  const clickSort = (col: DataTableColumn<T>) => {
    if (!hasSort || !col.sortable) return;

    const key = String(col.key);
    const currentSort = sort?.sort;
    const currentDir = sort?.direction ?? "asc";

    if (currentSort !== key) {
      onSortChange?.({ sort: key, direction: "asc" });
      return;
    }

    onSortChange?.({
      sort: key,
      direction: currentDir === "asc" ? "desc" : "asc",
    });
  };

  const colSpan =
    columns.length + (selectable ? 1 : 0) + (actions ? 1 : 0);

  return (
    <div className="datatable-wrapper">
      {/* TOOLBAR (layout antigo) */}
      <div className="datatable-toolbar">
        <div className="datatable-toolbar-left">
          {toolbar}
        </div>

        <div className="datatable-toolbar-right">
          {hasSearch && (
            <div className="datatable-search">
              <Search size={16} />
              <input
                placeholder="Buscar..."
                value={searchValue ?? ""}
                onChange={(e) => onSearchChange?.(e.target.value)}
              />
            </div>
          )}

          {hasPageSize && (
            <select
              className="datatable-pagesize"
              value={pagination!.pageSize}
              onChange={(e) =>
                onPageSizeChange?.(Number(e.target.value))
              }
            >
              {pageSizeOptions.map((n) => (
                <option key={n} value={n}>
                  {n} por página
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* TABLE CONTAINER (layout antigo) */}
      <div className="datatable-container">
        <table className="datatable">
          <thead>
            <tr>
              {selectable && (
                <th className="datatable-th-checkbox">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                    aria-label="Selecionar todos"
                  />
                </th>
              )}

              {columns.map((c) => {
                const key = String(c.key);
                const active = sort?.sort === key;
                const dir = sort?.direction ?? "asc";

                return (
                  <th
                    key={key}
                    className={[
                      c.sortable ? "sortable" : "",
                      active ? "active" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    style={c.width ? { width: c.width } : undefined}
                    onClick={() => clickSort(c)}
                  >
                    <span>{c.header}</span>

                    {c.sortable && (
                      <span className="sort-indicator">
                        {/* mostra direção apenas na coluna ativa */}
                        {active ? (dir === "asc" ? " ▲" : " ▼") : (
                          <span className="sort-icon">
                            <ArrowUpDown size={14} />
                          </span>
                        )}
                      </span>
                    )}
                  </th>
                );
              })}

              {actions && <th className="datatable-th-actions">Ações</th>}
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={colSpan} className="datatable-td-state">
                  <div className="datatable-state">Carregando...</div>
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={colSpan} className="datatable-td-state">
                  <div className="datatable-state">{emptyText}</div>
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => (
                <tr
                  key={selectable && getRowId ? getRowId(row) : idx}
                  className={isSelected(row) ? "selected" : ""}
                >
                  {selectable && (
                    <td className="datatable-td-checkbox">
                      <input
                        type="checkbox"
                        checked={isSelected(row)}
                        onChange={() => toggleRow(row)}
                        aria-label="Selecionar linha"
                      />
                    </td>
                  )}

                  {columns.map((c) => {
                    const k = String(c.key);
                    return (
                      <td key={k}>
                        {c.render
                          ? c.render(row)
                          : (row as any)[c.key as any] ?? "-"}
                      </td>
                    );
                  })}

                  {actions && (
                    <td className="datatable-td-actions">
                      {actions(row)}
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* mantém overlay do visual antigo */}
        {loading && (
          <div className="datatable-overlay">Carregando...</div>
        )}
      </div>

      {/* PAGINATION (layout antigo) */}
      {hasPagination && (
        <div className="datatable-pagination">
          <span>
            Página {pagination!.page} de {pagination!.totalPages} • Total:{" "}
            {pagination!.total}
          </span>

          <div className="datatable-pagination-actions">
            <button
              disabled={pagination!.page <= 1 || !!loading}
              onClick={() =>
                onPageChange?.(Math.max(1, pagination!.page - 1))
              }
              aria-label="Anterior"
            >
              <ChevronLeft size={16} />
              Anterior
            </button>

            <button
              disabled={
                pagination!.page >= pagination!.totalPages || !!loading
              }
              onClick={() =>
                onPageChange?.(
                  Math.min(pagination!.totalPages, pagination!.page + 1)
                )
              }
              aria-label="Próxima"
            >
              Próxima
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}