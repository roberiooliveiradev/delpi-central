import type { PurchaseOrdersQuery } from "./types";

/**
 * Active filters for Clear visibility.
 * Default authorized branch is NOT active by itself.
 * Page/page_size/order (detail deep-link) are navigation, not filters.
 */
export function hasActivePurchaseOrdersFilters(query: PurchaseOrdersQuery): boolean {
  return Boolean(
    query.order_number.trim() ||
      query.product_code.trim() ||
      query.supplier_code.trim() ||
      query.expected_delivery_from.trim() ||
      query.expected_delivery_to.trim() ||
      query.late_only,
  );
}
