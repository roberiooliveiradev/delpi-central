import { normalizeSuppliesUnitCode } from "../../app/suppliesUnits";
import { createDefaultQuery } from "./query";
import type { InventoryQuery } from "./types";

function sameUnitSet(left: readonly string[], right: readonly string[]): boolean {
  const a = left.map((unit) => normalizeSuppliesUnitCode(unit)).filter(Boolean);
  const b = right.map((unit) => normalizeSuppliesUnitCode(unit)).filter(Boolean);
  if (a.length !== b.length) return false;
  const set = new Set(a);
  return b.every((code) => set.has(code));
}

/** Clear visibility: «Todas» + no warehouse = default. Page/sort are navigation. */
export function hasActiveInventoryFilters(
  query: InventoryQuery,
  allowedUnits: readonly string[] = [],
): boolean {
  const defaults = createDefaultQuery();
  const isAllUnits =
    query.branches.length === 0 ||
    (allowedUnits.length > 0 && sameUnitSet(query.branches, allowedUnits));
  return Boolean(
    !isAllUnits ||
      query.warehouse.trim() !== defaults.warehouse.trim(),
  );
}
