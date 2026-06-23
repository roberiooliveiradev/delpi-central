import { useCallback, useMemo, useState, type ReactNode } from "react";
import { Search } from "lucide-react";

import { useClientPagination } from "../../hooks/useClientPagination";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { HelpTooltip } from "../HelpTooltip";
import { DataTable, type DataTableColumn } from "./DataTable";
import { LoadingActivityCard } from "../LoadingActivityCard";
import { Pagination, TablePageSizeSelect } from "../Pagination";
import { TABLE_PAGE_SIZE_OPTIONS } from "../../utils/paginationPages";

const DEFAULT_PAGE_SIZE = 20;

export type ServerPaginationConfig = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: readonly number[];
};

export type ServerSortConfig = {
  sortKey: string | null;
  sortDirection: "asc" | "desc";
  onSortChange: (columnKey: string) => void;
};

export type ServerSearchConfig = {
  value: string;
  onChange: (value: string) => void;
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
  titleHint?: string;
  hint?: string;
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  loading?: boolean;
  refreshing?: boolean;
  emptyMessage?: string;
  pageSize?: number;
  searchPlaceholder?: string;
  searchHint?: string;
  getSearchText?: (row: T) => string;
  hideSearch?: boolean;
  serverPagination?: ServerPaginationConfig;
  serverSort?: ServerSortConfig;
  serverSearch?: ServerSearchConfig;
  toolbarExtra?: ReactNode;
  onRowClick?: (row: T) => void;
  getRowClassName?: (row: T) => string | undefined;
  headerActions?: ReactNode;
};

export function DataTableSection<T>({
  title,
  titleHint,
  hint,
  columns,
  rows,
  rowKey,
  loading = false,
  refreshing = false,
  emptyMessage = "Nenhum registro encontrado.",
  pageSize = DEFAULT_PAGE_SIZE,
  searchPlaceholder = "Buscar na tabela…",
  searchHint,
  getSearchText,
  hideSearch = false,
  serverPagination,
  serverSort,
  serverSearch,
  toolbarExtra,
  onRowClick,
  getRowClassName,
  headerActions,
}: DataTableSectionProps<T>) {
  const [localSearch, setLocalSearch] = useState("");
  const [localPageSize, setLocalPageSize] = useState(pageSize);
  const search = serverSearch?.value ?? localSearch;
  const handleSearchChange = serverSearch?.onChange ?? setLocalSearch;
  const effectivePageSize = serverPagination?.pageSize ?? localPageSize;
  const pageSizeOptions =
    serverPagination?.pageSizeOptions ?? TABLE_PAGE_SIZE_OPTIONS;

  const filteredRows = useMemo(() => {
    if (serverPagination) return rows;

    const query = search.trim().toLowerCase();
    if (!query) return rows;

    return rows.filter((row) => {
      const haystack = (getSearchText ?? ((item) => buildSearchText(item, columns)))(
        row
      ).toLowerCase();
      return haystack.includes(query);
    });
  }, [rows, search, columns, getSearchText, serverPagination]);

  const { page, setPage, slice, total } = useClientPagination(
    filteredRows,
    effectivePageSize
  );
  const displayRows = serverPagination ? rows : slice;
  const paginationPage = serverPagination?.page ?? page;
  const paginationTotal = serverPagination?.total ?? total;
  const paginationSize = serverPagination?.pageSize ?? effectivePageSize;
  const handlePageChange = serverPagination?.onPageChange ?? setPage;
  const handlePageSizeChange = useCallback(
    (nextPageSize: number) => {
      if (serverPagination?.onPageSizeChange) {
        serverPagination.onPageSizeChange(nextPageSize);
        return;
      }

      setLocalPageSize(nextPageSize);
      setPage(1);
    },
    [serverPagination, setPage],
  );

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
    <section className="dc-card dc-table-section" aria-busy={loading || refreshing}>
      <div className="dc-table-section__header">
        <h2 className="dc-section-title">
          {title}
          {titleHint ? (
            <HelpTooltip
              content={titleHint}
              ariaLabel={`Ajuda: ${title}`}
              className="dc-table-section__title-help"
            />
          ) : null}
        </h2>
        <div className="dc-table-section__meta-group">
          {hint ? <span className="dc-table-section__meta">{hint}</span> : null}
          <span className="dc-table-section__meta">
            {paginationTotal} registro(s)
          </span>
          {headerActions ? (
            <div className="dc-table-section__actions dc-no-print">{headerActions}</div>
          ) : null}
        </div>
      </div>

      {showRefreshLoading ? (
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
          <div className="dc-table-toolbar">
            <TablePageSizeSelect
              pageSize={paginationSize}
              pageSizeOptions={pageSizeOptions}
              onPageSizeChange={handlePageSizeChange}
            />

            {!hideSearch ? (
              <div className="dc-table-toolbar__search-group">
                <div className="dc-table-search" role="search">
                  <Search
                    size={16}
                    aria-hidden="true"
                    className="dc-table-search__icon"
                  />
                  <input
                    type="search"
                    className="dc-table-search__input"
                    value={search}
                    placeholder={searchPlaceholder}
                    onChange={(event) => handleSearchChange(event.target.value)}
                    aria-label="Filtrar registros da tabela"
                  />
                </div>
                {searchHint ? (
                  <HelpTooltip
                    content={searchHint}
                    ariaLabel="Ajuda: busca na tabela"
                    className="dc-table-search__help"
                  />
                ) : null}
              </div>
            ) : null}

            {toolbarExtra ? (
              <div className="dc-table-toolbar__extra">{toolbarExtra}</div>
            ) : null}
          </div>

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
            layout="section"
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
