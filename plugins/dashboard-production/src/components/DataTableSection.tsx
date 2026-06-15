import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { useClientPagination } from "../hooks/useClientPagination";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import { DataTable, type DataTableColumn } from "./DataTable";
import { HelpTooltip } from "./HelpTooltip";
import { LoadingActivityCard } from "./LoadingActivityCard";
import { Pagination } from "./Pagination";

const DEFAULT_PAGE_SIZE = 20;

export type ServerPaginationConfig = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

export type ServerSortConfig = {
  sortKey: string | null;
  sortDirection: "asc" | "desc";
  onSortChange: (columnKey: string) => void;
};

function buildSearchText<T>(row: T, columns: DataTableColumn<T>[]): string {
  return columns
    .map((column) => {
      const value = column.render(row);
      if (value == null || value === false) return "";
      if (typeof value === "string" || typeof value === "number") {
        return String(value);
      }
      return "";
    })
    .join(" ")
    .toLowerCase();
}

export type DataTableSectionProps<T> = {
  title: string;
  hint?: string;
  titleHint?: string;
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  loading?: boolean;
  refreshing?: boolean;
  emptyMessage?: string;
  pageSize?: number;
  searchPlaceholder?: string;
  getSearchText?: (row: T) => string;
  hideSearch?: boolean;
  serverPagination?: ServerPaginationConfig;
  serverSort?: ServerSortConfig;
  headerActions?: ReactNode;
  onRowClick?: (row: T) => void;
  getRowClassName?: (row: T) => string | undefined;
};

export function DataTableSection<T>({
  title,
  hint,
  titleHint,
  columns,
  rows,
  rowKey,
  loading = false,
  refreshing = false,
  emptyMessage = "Nenhum registro encontrado.",
  pageSize = DEFAULT_PAGE_SIZE,
  searchPlaceholder = "Buscar na tabela…",
  getSearchText,
  hideSearch = false,
  serverPagination,
  serverSort,
  headerActions,
  onRowClick,
  getRowClassName,
}: DataTableSectionProps<T>) {
  const [search, setSearch] = useState("");

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return rows;

    return rows.filter((row) => {
      const haystack = (getSearchText ?? ((item) => buildSearchText(item, columns)))(
        row
      ).toLowerCase();
      return haystack.includes(query);
    });
  }, [rows, search, columns, getSearchText]);

  const { page, setPage, slice, total } = useClientPagination(
    filteredRows,
    pageSize
  );

  useEffect(() => {
    if (serverPagination && search.trim()) {
      serverPagination.onPageChange(1);
    }
  }, [search, serverPagination]);

  const displayRows = serverPagination ? filteredRows : slice;
  const paginationPage = serverPagination?.page ?? page;
  const paginationTotal = serverPagination?.total ?? total;
  const paginationSize = serverPagination?.pageSize ?? pageSize;
  const handlePageChange = serverPagination?.onPageChange ?? setPage;

  const showInitialLoading = loading && rows.length === 0;
  const showRefreshLoading = refreshing && rows.length > 0;
  const initialFetchProgress = useTrackedSingleFetchProgress(showInitialLoading);
  const refreshFetchProgress = useTrackedSingleFetchProgress(showRefreshLoading);
  const initialLoadingProgress = useLoadingProgress(
    showInitialLoading,
    initialFetchProgress
  );
  const refreshLoadingProgress = useLoadingProgress(
    showRefreshLoading,
    refreshFetchProgress
  );

  return (
    <section
      className="dp-card dp-table-section"
      aria-busy={loading || refreshing}
    >
      <div className="dp-table-section__header">
        <h2 className="dp-section-title">
          {title}
          {titleHint ? (
            <HelpTooltip
              content={titleHint}
              ariaLabel={`Ajuda: ${title}`}
              className="dp-section-title__help"
            />
          ) : null}
        </h2>
        <div className="dp-table-section__meta-group">
          {hint ? <span className="dp-table-section__meta">{hint}</span> : null}
          <span className="dp-table-section__meta">
            {paginationTotal} registro(s)
          </span>
          {headerActions}
        </div>
      </div>

      {refreshing && rows.length > 0 ? (
        <LoadingActivityCard
          title="Atualizando tabela"
          description="Mantendo os dados visíveis enquanto a nova consulta é aplicada."
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      {showInitialLoading ? (
        <LoadingActivityCard
          title="Carregando registros"
          description="Aguarde enquanto os dados da tabela são obtidos."
          progressPercent={initialLoadingProgress}
        />
      ) : (
        <>
          {!hideSearch ? (
            <div className="dp-table-toolbar">
              <div className="dp-table-search" role="search">
                <Search size={16} aria-hidden="true" className="dp-table-search__icon" />
                <input
                  type="search"
                  className="dp-table-search__input"
                  value={search}
                  placeholder={searchPlaceholder}
                  onChange={(event) => setSearch(event.target.value)}
                  aria-label="Filtrar registros da tabela"
                />
              </div>
            </div>
          ) : null}

          <DataTable
            columns={columns}
            rows={displayRows}
            rowKey={rowKey}
            emptyMessage={emptyMessage}
            onRowClick={onRowClick}
            getRowClassName={getRowClassName}
            sortKey={serverSort?.sortKey}
            sortDirection={serverSort?.sortDirection}
            onSortChange={serverSort?.onSortChange}
          />

          <Pagination
            page={paginationPage}
            pageSize={paginationSize}
            total={paginationTotal}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </section>
  );
}
