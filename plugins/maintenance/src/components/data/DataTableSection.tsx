import { useEffect, useMemo, useState, type ReactNode } from "react";

import { useClientPagination } from "../../hooks/useClientPagination";
import { sortRows } from "../../utils/dataTableSort";
import { DataTable } from "./DataTable";
import { Pagination } from "./Pagination";
import type { DataTableColumn, ServerPaginationConfig, ServerTableConfig } from "./types";

export const DEFAULT_TABLE_PAGE_SIZE = 20;

type DataTableSectionProps<T> = {
  title: string;
  hint?: string;
  /** Sobrescreve o badge automático de contagem. */
  badge?: ReactNode;
  /** Sufixo do badge automático quando `badge` não é informado. Padrão: registro(s). */
  countBadgeLabel?: string;
  actions?: ReactNode;
  toolbar?: ReactNode;
  columns: DataTableColumn<T>[];
  rows: T[];
  loading?: boolean;
  emptyMessage?: string;
  getRowKey: (row: T, index: number) => string;
  getRowClassName?: (row: T) => string | undefined;
  embedded?: boolean;
  onRowClick?: (row: T) => void;
  pageSize?: number;
  /** @deprecated Prefer serverTable */
  serverPagination?: ServerPaginationConfig;
  serverTable?: ServerTableConfig;
  defaultSortKey?: string;
  defaultSortDirection?: "asc" | "desc";
  hidePaginationWhenSinglePage?: boolean;
};

export function DataTableSection<T>({
  title,
  hint,
  badge,
  countBadgeLabel = "registro(s)",
  actions,
  toolbar,
  columns,
  rows,
  loading = false,
  emptyMessage,
  getRowKey,
  getRowClassName,
  embedded = false,
  onRowClick,
  pageSize = DEFAULT_TABLE_PAGE_SIZE,
  serverPagination,
  serverTable,
  defaultSortKey,
  defaultSortDirection = "asc",
  hidePaginationWhenSinglePage = false,
}: DataTableSectionProps<T>) {
  const serverMode = serverTable ?? serverPagination;
  const isFullServerTable = Boolean(serverTable);

  const [sortKey, setSortKey] = useState<string | null>(defaultSortKey ?? null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">(defaultSortDirection);

  useEffect(() => {
    if (isFullServerTable) return;
    setSortKey(defaultSortKey ?? null);
  }, [defaultSortKey, isFullServerTable]);

  useEffect(() => {
    if (isFullServerTable) return;
    setSortDirection(defaultSortDirection);
  }, [defaultSortDirection, isFullServerTable]);

  const activeSortKey = isFullServerTable ? serverTable!.sortKey : sortKey;
  const activeSortDirection = isFullServerTable ? serverTable!.sortDirection : sortDirection;

  const sortedRows = useMemo(() => {
    if (serverMode) return rows;
    if (!sortKey) return rows;
    return sortRows(rows, columns, sortKey, sortDirection);
  }, [rows, columns, sortKey, sortDirection, serverMode]);

  const clientPagination = useClientPagination(serverMode ? [] : sortedRows, pageSize);

  const displayRows = serverMode ? rows : clientPagination.slice;
  const paginationPage = serverMode?.page ?? clientPagination.page;
  const paginationPageSize = serverMode?.pageSize ?? clientPagination.pageSize;
  const paginationTotal = serverMode?.total ?? clientPagination.total;
  const handlePageChange =
    serverMode?.onPageChange ?? ((nextPage: number) => clientPagination.setPage(nextPage));

  const resolvedBadge = badge ?? `${paginationTotal} ${countBadgeLabel}`;

  useEffect(() => {
    if (!serverMode) {
      clientPagination.setPage(1);
    }
  }, [sortKey, sortDirection, serverMode]);

  const handleSortChange = (columnKey: string) => {
    if (isFullServerTable) {
      serverTable!.onSortChange(columnKey);
      return;
    }

    const isSameColumn = sortKey === columnKey;
    const nextDirection = isSameColumn ? (sortDirection === "asc" ? "desc" : "asc") : "asc";
    setSortKey(columnKey);
    setSortDirection(nextDirection);
    if (serverPagination) {
      serverPagination.onPageChange(1);
      return;
    }
    clientPagination.setPage(1);
  };

  const content = (
    <>
      <div className="dm-section-header">
        <div className="dm-section-header__title-group">
          <h3 className="dm-section-header__title">{title}</h3>
          {hint ? <p className="dm-section-header__hint">{hint}</p> : null}
        </div>
        <div className="dm-section-header__meta">
          <span className="dm-badge">{resolvedBadge}</span>
          {actions}
        </div>
      </div>

      {toolbar ? <div className="dm-section-toolbar">{toolbar}</div> : null}

      <DataTable
        columns={columns}
        rows={displayRows}
        loading={loading}
        emptyMessage={emptyMessage}
        getRowKey={getRowKey}
        getRowClassName={getRowClassName}
        onRowClick={onRowClick}
        sortKey={activeSortKey}
        sortDirection={activeSortDirection}
        onSortChange={handleSortChange}
      />

      {!loading && paginationTotal > 0 ? (
        <Pagination
          page={paginationPage}
          pageSize={paginationPageSize}
          total={paginationTotal}
          onPageChange={handlePageChange}
          hideWhenSinglePage={hidePaginationWhenSinglePage}
        />
      ) : null}
    </>
  );

  if (embedded) {
    return <section className="dm-table-section dm-table-section--embedded">{content}</section>;
  }

  return <section className="dm-card dm-table-section">{content}</section>;
}
