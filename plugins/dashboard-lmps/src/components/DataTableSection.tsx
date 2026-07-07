import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { HelpTooltip } from "@delpi/plugin-ui";
import { useClientPagination } from "../hooks/useClientPagination";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import { DataTable, type DataTableColumn } from "./dataTableUi";
import { LoadingActivityCard } from "./LoadingActivityCard";
import { Pagination } from "./Pagination";
import { sortTableRows } from "../utils/sortTableRows";

const DEFAULT_PAGE_SIZE = 20;

export type ServerPaginationConfig = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

export type ClientSortConfig = {
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
  clientSort?: ClientSortConfig;
  onRowClick?: (row: T) => void;
  getRowClassName?: (row: T) => string | undefined;
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
  clientSort,
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

  const sortedRows = useMemo(() => {
    if (!clientSort) return filteredRows;

    return sortTableRows(
      filteredRows,
      columns,
      clientSort.sortKey,
      clientSort.sortDirection
    );
  }, [filteredRows, columns, clientSort]);

  const { page, setPage, slice, total } = useClientPagination(
    sortedRows,
    pageSize
  );

  useEffect(() => {
    if (serverPagination && search.trim()) {
      serverPagination.onPageChange(1);
    }
  }, [search, serverPagination]);

  const displayRows = serverPagination ? sortedRows : slice;
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
      className="lmps-card lmps-table-section"
      aria-busy={loading || refreshing}
    >
      <div className="lmps-table-section__header">
        <h2 className="lmps-section-title">
          {title}
          {titleHint ? (
            <HelpTooltip
              content={titleHint}
              ariaLabel={`Ajuda: ${title}`}
              className="lmps-table-section__title-help"
            />
          ) : null}
        </h2>
        <div className="lmps-table-section__meta-group">
          {hint ? <span className="lmps-table-section__meta">{hint}</span> : null}
          <span className="lmps-table-section__meta">
            {paginationTotal} registro(s)
          </span>
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
            <div className="lmps-table-toolbar">
              <div className="lmps-table-search" role="search">
                <Search size={16} aria-hidden="true" className="lmps-table-search__icon" />
                <input
                  type="search"
                  className="lmps-table-search__input"
                  value={search}
                  placeholder={searchPlaceholder}
                  onChange={(event) => setSearch(event.target.value)}
                  aria-label="Filtrar registros da tabela"
                />
              </div>
              {searchHint ? (
                <HelpTooltip
                  content={searchHint}
                  ariaLabel="Ajuda: busca na tabela"
                  className="lmps-table-search__help"
                />
              ) : null}
            </div>
          ) : null}

          <DataTable
            columns={columns}
            rows={displayRows}
            rowKey={rowKey}
            emptyMessage={emptyMessage}
            onRowClick={onRowClick}
            getRowClassName={getRowClassName}
            sortKey={clientSort?.sortKey}
            sortDirection={clientSort?.sortDirection}
            onSortChange={clientSort?.onSortChange}
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
