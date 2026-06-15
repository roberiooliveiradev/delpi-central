import { useCallback, useState } from "react";

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
    pageSize: options.pageSize ?? 20,
    sortKey: options.defaultSortKey ?? null,
    sortDirection: options.defaultSortDirection ?? "asc",
  });

  const setPage = useCallback((page: number) => {
    setQuery((current) => ({ ...current, page: Math.max(1, page) }));
  }, []);

  const resetPage = useCallback(() => {
    setQuery((current) => ({ ...current, page: 1 }));
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

  return {
    query,
    setPage,
    resetPage,
    handleSortChange,
  };
}
