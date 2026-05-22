import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Search } from "lucide-react";

import { useClientPagination } from "../hooks/useClientPagination";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import { DataTable, type DataTableColumn } from "./DataTable";
import { LoadingActivityCard } from "./LoadingActivityCard";
import { Pagination } from "./Pagination";

export const DEFAULT_TABLE_PAGE_SIZE = 20;

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
  onRowClick?: (row: T) => void;
  getRowClassName?: (row: T) => string | undefined;
  footer?: ReactNode;
  interactive?: boolean;
};

export function DataTableSection<T>({
  title,
  hint,
  columns,
  rows,
  rowKey,
  loading = false,
  refreshing = false,
  emptyMessage = "Nenhum registro encontrado.",
  pageSize = DEFAULT_TABLE_PAGE_SIZE,
  searchPlaceholder = "Buscar na tabela…",
  getSearchText,
  hideSearch = false,
  onRowClick,
  getRowClassName,
  footer,
  interactive = Boolean(onRowClick),
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

  const { page, setPage, slice, total } = useClientPagination(filteredRows, pageSize);

  useEffect(() => {
    setPage(1);
  }, [search]);

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

  const sectionClass = [
    "ds-card",
    "ds-table-section",
    interactive ? "ds-table-section--interactive" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section className={sectionClass} aria-busy={loading || refreshing}>
      <div className="ds-table-section__header">
        <h2 className="ds-section-title">{title}</h2>
        <div className="ds-table-section__meta-group">
          {hint ? <span className="ds-table-section__meta">{hint}</span> : null}
          <span className="ds-table-section__meta">{total} registro(s)</span>
        </div>
      </div>

      {footer ? <div className="ds-table-section__footer">{footer}</div> : null}

      {refreshing && rows.length > 0 ? (
        <LoadingActivityCard
          title="Atualizando tabela"
          description="Mantendo os dados visíveis enquanto a consulta é aplicada."
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
            <div className="ds-table-toolbar">
              <div className="ds-table-search" role="search">
                <Search size={16} aria-hidden="true" className="ds-table-search__icon" />
                <input
                  type="search"
                  className="ds-table-search__input"
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
            rows={slice}
            rowKey={rowKey}
            emptyMessage={emptyMessage}
            onRowClick={onRowClick}
            getRowClassName={getRowClassName}
          />

          <Pagination
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={setPage}
          />
        </>
      )}
    </section>
  );
}
