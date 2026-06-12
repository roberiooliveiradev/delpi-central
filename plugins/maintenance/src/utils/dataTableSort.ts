import { isValidElement, type ReactNode } from "react";

import type { DataTableColumn } from "../components/data/types";

export function extractTextFromNode(node: ReactNode): string {
  if (node == null || typeof node === "boolean") return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(extractTextFromNode).join(" ");
  if (isValidElement<{ children?: ReactNode }>(node)) {
    return extractTextFromNode(node.props.children);
  }
  return "";
}

export function sortRows<T>(
  rows: T[],
  columns: DataTableColumn<T>[],
  sortKey: string,
  sortDirection: "asc" | "desc",
): T[] {
  const column = columns.find((item) => item.key === sortKey);
  if (!column) return rows;

  const getSortValue =
    column.sortValue ??
    ((row: T): string | number | boolean => {
      const value = column.render(row);
      if (value == null || value === false) return "";
      if (typeof value === "number" || typeof value === "boolean") return value;
      if (typeof value === "string") return value.toLowerCase();
      return extractTextFromNode(value).toLowerCase();
    });

  const directionFactor = sortDirection === "asc" ? 1 : -1;

  return [...rows].sort((first, second) => {
    const firstValue = getSortValue(first);
    const secondValue = getSortValue(second);

    if (firstValue == null && secondValue == null) return 0;
    if (firstValue == null) return 1 * directionFactor;
    if (secondValue == null) return -1 * directionFactor;
    if (typeof firstValue === "number" && typeof secondValue === "number") {
      return (firstValue - secondValue) * directionFactor;
    }

    const firstText = String(firstValue).toLowerCase();
    const secondText = String(secondValue).toLowerCase();
    if (firstText < secondText) return -1 * directionFactor;
    if (firstText > secondText) return 1 * directionFactor;
    return 0;
  });
}
