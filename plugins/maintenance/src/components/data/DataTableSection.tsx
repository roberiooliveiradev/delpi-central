import { useEffect, useMemo, useState, type ReactNode } from "react";

import { useClientPagination } from "../../hooks/useClientPagination";
import { sortRows } from "../../utils/dataTableSort";
import { DataTable } from "./DataTable";
import { Pagination } from "./Pagination";
import type { DataTableColumn, ServerPaginationConfig } from "./types";

export const DEFAULT_TABLE_PAGE_SIZE = 20;

type DataTableSectionProps<T> = {
  title: string;
  hint?: string;
  badge?: ReactNode;
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
  serverPagination?: ServerPaginationConfig;
  defaultSortKey?: string;
  defaultSortDirection?: "asc" | "desc";
  hidePaginationWhenSinglePage?: boolean;
};

export function DataTableSection<T>({
  title,
  hint,
  badge,
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
  defaultSortKey,
  defaultSortDirection = "asc",
  hidePaginationWhenSinglePage = false,
}: DataTableSectionProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(defaultSortKey ?? null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">(defaultSortDirection);

  useEffect(() => {
    setSortKey(defaultSortKey ?? null);
  }, [defaultSortKey]);

  useEffect(() => {
    setSortDirection(defaultSortDirection);
  }, [defaultSortDirection]);

  const sortedRows = useMemo(() => {
    if (!sortKey) return rows;
    return sortRows(rows, columns, sortKey, sortDirection);
  }, [rows, columns, sortKey, sortDirection]);

  const clientPagination = useClientPagination(
    serverPagination ? [] : sortedRows,
    pageSize,
  );

  const displayRows = serverPagination ? sortedRows : clientPagination.slice;
  const paginationPage = serverPagination?.page ?? clientPagination.page;
  const paginationPageSize = serverPagination?.pageSize ?? clientPagination.pageSize;
  const paginationTotal = serverPagination?.total ?? clientPagination.total;
  const handlePageChange =
    serverPagination?.onPageChange ?? ((nextPage: number) => clientPagination.setPage(nextPage));

  useEffect(() => {
    if (!serverPagination) {
      clientPagination.setPage(1);
    }
  }, [sortKey, sortDirection, serverPagination]);

  const handleSortChange = (columnKey: string) => {
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
          {badge ? <span className="dm-badge">{badge}</span> : null}
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
        sortKey={sortKey}
        sortDirection={sortDirection}
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
