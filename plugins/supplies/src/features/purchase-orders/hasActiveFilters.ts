import { normalizeSuppliesUnitCode } from "../../app/suppliesUnits";
import type { PurchaseOrdersQuery } from "./types";

function sameUnitSet(left: readonly string[], right: readonly string[]): boolean {
  const a = left.map((unit) => normalizeSuppliesUnitCode(unit)).filter(Boolean);
  const b = right.map((unit) => normalizeSuppliesUnitCode(unit)).filter(Boolean);
  if (a.length !== b.length) return false;
  const set = new Set(a);
  return b.every((code) => set.has(code));
}

/**
 * Active filters for Clear visibility.
 * Empty MultiSelect («Todas») or selecting every authorized unit is NOT active by itself.
 * Page/page_size/order/sort are navigation, not filters.
 */
export function hasActivePurchaseOrdersFilters(
  query: PurchaseOrdersQuery,
  allowedUnits: readonly string[] = [],
): boolean {
  const isAllUnits =
    query.branches.length === 0 ||
    (allowedUnits.length > 0 && sameUnitSet(query.branches, allowedUnits));
  return Boolean(
    !isAllUnits ||
      query.order_number.trim() ||
      query.product_code.trim() ||
      query.supplier_code.trim() ||
      query.expected_delivery_from.trim() ||
      query.expected_delivery_to.trim() ||
      query.late_only,
  );
}
