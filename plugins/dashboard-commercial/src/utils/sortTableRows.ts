import type { DataTableColumn } from "../components/table";

function compareSortValues(
  left: string | number | null | undefined,
  right: string | number | null | undefined
): number {
  if (left == null && right == null) return 0;
  if (left == null) return 1;
  if (right == null) return -1;

  if (typeof left === "number" && typeof right === "number") {
    return left - right;
  }

  return String(left).localeCompare(String(right), "pt-BR", {
    sensitivity: "base",
    numeric: true,
  });
}

export function sortTableRows<T>(
  rows: T[],
  columns: DataTableColumn<T>[],
  sortKey: string | null,
  sortDirection: "asc" | "desc"
): T[] {
  if (!sortKey) return rows;

  const column = columns.find((entry) => entry.key === sortKey);
  if (!column?.sortable || !column.sortValue) return rows;

  const direction = sortDirection === "asc" ? 1 : -1;

  return [...rows].sort(
    (left, right) =>
      compareSortValues(column.sortValue!(left), column.sortValue!(right)) *
      direction
  );
}
