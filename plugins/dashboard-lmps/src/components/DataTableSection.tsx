import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { HelpTooltip, NativeTextControl, dataTableSectionBemClasses } from "@delpi/plugin-ui/index";
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
const LMPS_SECTION = dataTableSectionBemClasses("lmps");


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
      className={LMPS_SECTION.section}
      aria-busy={loading || refreshing}
    >
      <div className={LMPS_SECTION.header}>
        <h2 className={LMPS_SECTION.title}>
          {title}
          {titleHint ? (
            <HelpTooltip
              content={titleHint}
              ariaLabel={`Ajuda: ${title}`}
              className={LMPS_SECTION.titleHelp}
            />
          ) : null}
        </h2>
        <div className={LMPS_SECTION.metaGroup}>
          {hint ? <span className={LMPS_SECTION.meta}>{hint}</span> : null}
          <span className={LMPS_SECTION.meta}>
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
            <div className={LMPS_SECTION.toolbar}>
              <div className={LMPS_SECTION.search} role="search">
                <Search size={16} aria-hidden="true" className={LMPS_SECTION.searchIcon} />
                <NativeTextControl
                  type="search"
                  className={LMPS_SECTION.searchInput}
                  value={search}
                  placeholder={searchPlaceholder}
                  onChange={setSearch}
                  aria-label="Filtrar registros da tabela"
                />
              </div>
              {searchHint ? (
                <HelpTooltip
                  content={searchHint}
                  ariaLabel="Ajuda: busca na tabela"
                  className={LMPS_SECTION.searchHelp}
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
