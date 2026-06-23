import { useCallback, useState } from "react";

type UseClientTableSortOptions = {
  defaultSortKey?: string;
  defaultSortDirection?: "asc" | "desc";
};

export function useClientTableSort(options: UseClientTableSortOptions = {}) {
  const [sortKey, setSortKey] = useState<string | null>(
    options.defaultSortKey ?? null
  );
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">(
    options.defaultSortDirection ?? "asc"
  );

  const handleSortChange = useCallback((columnKey: string) => {
    setSortKey((currentKey) => {
      if (currentKey === columnKey) {
        setSortDirection((currentDirection) =>
          currentDirection === "asc" ? "desc" : "asc"
        );
        return currentKey;
      }

      setSortDirection("asc");
      return columnKey;
    });
  }, []);

  return {
    sortKey,
    sortDirection,
    handleSortChange,
  };
}
