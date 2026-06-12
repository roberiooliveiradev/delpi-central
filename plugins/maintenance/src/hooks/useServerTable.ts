import { useCallback, useState } from "react";

import { DEFAULT_TABLE_PAGE_SIZE } from "../components/data/DataTableSection";

export type ServerTableQuery = {
  page: number;
  pageSize: number;
  sortKey: string | null;
  sortDirection: "asc" | "desc";
};

type UseServerTableOptions = {
  defaultSortKey?: string;
  defaultSortDirection?: "asc" | "desc";
  pageSize?: number;
};

export function useServerTable(options: UseServerTableOptions = {}) {
  const [query, setQuery] = useState<ServerTableQuery>({
    page: 1,
    pageSize: options.pageSize ?? DEFAULT_TABLE_PAGE_SIZE,
    sortKey: options.defaultSortKey ?? null,
    sortDirection: options.defaultSortDirection ?? "asc",
  });

  const setPage = useCallback((page: number) => {
    setQuery((current) => ({ ...current, page: Math.max(1, page) }));
  }, []);

  const resetPage = useCallback(() => {
    setQuery((current) => ({ ...current, page: 1 }));
  }, []);

  const setSort = useCallback((sortKey: string, sortDirection: "asc" | "desc") => {
    setQuery((current) => ({
      ...current,
      page: 1,
      sortKey,
      sortDirection,
    }));
  }, []);

  const handleSortChange = useCallback((columnKey: string) => {
    setQuery((current) => {
      const isSameColumn = current.sortKey === columnKey;
      const nextDirection = isSameColumn
        ? current.sortDirection === "asc"
          ? "desc"
          : "asc"
        : "asc";
      return {
        ...current,
        page: 1,
        sortKey: columnKey,
        sortDirection: nextDirection,
      };
    });
  }, []);

  const replaceQuery = useCallback((next: Partial<ServerTableQuery>) => {
    setQuery((current) => ({
      ...current,
      ...next,
      page: next.page ?? current.page,
    }));
  }, []);

  return {
    query,
    setPage,
    resetPage,
    setSort,
    handleSortChange,
    replaceQuery,
  };
}
