import type { DataTableColumn } from "@delpi/plugin-ui/index";

export type TableSortDirection = "asc" | "desc";

function compareSortValues(
  left: string | number | boolean | null | undefined,
  right: string | number | boolean | null | undefined,
): number {
  if (left == null && right == null) return 0;
  if (left == null) return 1;
  if (right == null) return -1;

  if (typeof left === "number" && typeof right === "number") {
    return left - right;
  }
  if (typeof left === "boolean" && typeof right === "boolean") {
    return Number(left) - Number(right);
  }

  return String(left).localeCompare(String(right), "pt-BR", {
    sensitivity: "base",
    numeric: true,
  });
}

/**
 * Ordenação client-side alinhada ao DataTableSection do kit
 * (exige `sortable` + `sortValue` na coluna).
 */
export function sortTableRows<T>(
  rows: readonly T[],
  columns: DataTableColumn<T>[],
  sortKey: string | null,
  sortDirection: TableSortDirection,
): T[] {
  if (!sortKey) return [...rows];

  const column = columns.find((entry) => entry.key === sortKey);
  if (!column?.sortable || !column.sortValue) return [...rows];

  const direction = sortDirection === "asc" ? 1 : -1;

  return [...rows].sort(
    (left, right) =>
      compareSortValues(column.sortValue!(left), column.sortValue!(right)) * direction,
  );
}

/** Clique no header: mesma coluna inverte direção; coluna nova usa `defaultDirection`. */
export function nextTableSortState(
  currentKey: string | null,
  currentDirection: TableSortDirection,
  nextKey: string,
  defaultDirection: TableSortDirection = "desc",
): { sortKey: string; sortDirection: TableSortDirection } {
  if (currentKey === nextKey) {
    return {
      sortKey: nextKey,
      sortDirection: currentDirection === "asc" ? "desc" : "asc",
    };
  }
  return { sortKey: nextKey, sortDirection: defaultDirection };
}
