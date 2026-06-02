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
  filters?: ReactNode;
  defaultSortKey?: string;
  defaultSortDirection?: "asc" | "desc";
  onSortChange?: (columnKey: string, direction: "asc" | "desc") => void;
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
  filters,
  defaultSortKey,
  defaultSortDirection = "asc",
  onSortChange,
  onRowClick,
  getRowClassName,
  footer,
  interactive = Boolean(onRowClick),
}: DataTableSectionProps<T>) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(defaultSortKey ?? null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">(
    defaultSortDirection
  );

  useEffect(() => {
    setSortKey(defaultSortKey ?? null);
  }, [defaultSortKey]);

  useEffect(() => {
    setSortDirection(defaultSortDirection);
  }, [defaultSortDirection]);

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
    if (!sortKey) return filteredRows;
    if (onSortChange) return filteredRows;

    const column = columns.find((item) => item.key === sortKey);
    if (!column) return filteredRows;

    const getSortValue = column.sortValue
      ? column.sortValue
      : (row: T): string | number | boolean => {
          const value = column.render(row);
          if (value == null || value === false) return "";
          if (typeof value === "number" || typeof value === "boolean") return value;
          if (typeof value === "string") return value.toLowerCase();
          return "";
        };

    const directionFactor = sortDirection === "asc" ? 1 : -1;

    return [...filteredRows].sort((first, second) => {
      const firstValue = getSortValue(first);
      const secondValue = getSortValue(second);

      if (firstValue == null && secondValue == null) return 0;
      if (firstValue == null) return 1 * directionFactor;
      if (secondValue == null) return -1 * directionFactor;
      if (
        typeof firstValue === "number" &&
        typeof secondValue === "number"
      ) {
        return (firstValue - secondValue) * directionFactor;
      }

      const firstText = String(firstValue).toLowerCase();
      const secondText = String(secondValue).toLowerCase();
      if (firstText < secondText) return -1 * directionFactor;
      if (firstText > secondText) return 1 * directionFactor;
      return 0;
    });
  }, [filteredRows, sortKey, sortDirection, columns, onSortChange]);

  const { page, setPage, slice, total } = useClientPagination(sortedRows, pageSize);

  useEffect(() => {
    setPage(1);
  }, [search]);

  useEffect(() => {
    if (!onSortChange) {
      setPage(1);
    }
  }, [sortKey, sortDirection, onSortChange, setPage]);

  const handleSortChange = (columnKey: string) => {
    const isSameColumn = sortKey === columnKey;
    const nextDirection = isSameColumn
      ? sortDirection === "asc"
        ? "desc"
        : "asc"
      : "asc";

    if (onSortChange) {
      onSortChange(columnKey, nextDirection);
      return;
    }

    setSortKey(columnKey);
    setSortDirection(nextDirection);
  };

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
          {(!hideSearch || filters) ? (
            <div className="ds-table-toolbar">
              {!hideSearch ? (
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
              ) : null}
              {filters ? <div className="ds-table-toolbar__filters">{filters}</div> : null}
            </div>
          ) : null}

          <DataTable
            columns={columns}
            rows={slice}
            rowKey={rowKey}
            emptyMessage={emptyMessage}
            onRowClick={onRowClick}
            getRowClassName={getRowClassName}
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSortChange={handleSortChange}
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
