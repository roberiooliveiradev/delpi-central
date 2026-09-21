import { normalizeSuppliesUnitCode } from "../../app/suppliesUnits";
import { createDefaultQuery } from "./query";
import type { DeliveriesQuery } from "./types";

function sameUnitSet(left: readonly string[], right: readonly string[]): boolean {
  const a = left.map((unit) => normalizeSuppliesUnitCode(unit)).filter(Boolean);
  const b = right.map((unit) => normalizeSuppliesUnitCode(unit)).filter(Boolean);
  if (a.length !== b.length) return false;
  const set = new Set(a);
  return b.every((code) => set.has(code));
}

/**
 * Clear visibility: «Todas» + status late + mês corrente = default (not active).
 * Page/page_size/sort are navigation, not filters.
 */
export function hasActiveDeliveriesFilters(
  query: DeliveriesQuery,
  allowedUnits: readonly string[] = [],
  now: Date = new Date(),
): boolean {
  const defaults = createDefaultQuery([], now);
  const isAllUnits =
    query.branches.length === 0 ||
    (allowedUnits.length > 0 && sameUnitSet(query.branches, allowedUnits));
  return Boolean(
    !isAllUnits ||
      query.status !== defaults.status ||
      query.start_date.trim() !== defaults.start_date ||
      query.end_date.trim() !== defaults.end_date,
  );
}
