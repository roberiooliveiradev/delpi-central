import { createDefaultQuery } from "./query";
import type { PurchaseRequestsQuery } from "./types";

/**
 * Active filters for Clear visibility.
 * Default authorized branch is NOT active by itself.
 * Default rolling period (date_from/date_to) is baseline, not active.
 * Page/page_size/request (inline detail) are navigation, not filters.
 */
export function hasActivePurchaseRequestsFilters(query: PurchaseRequestsQuery): boolean {
  const defaults = createDefaultQuery(query.branch || "");
  const periodChanged =
    query.date_from.trim() !== defaults.date_from ||
    query.date_to.trim() !== defaults.date_to;
  return Boolean(
    query.request_number.trim() ||
      query.product_code.trim() ||
      query.overall_stages.length > 0 ||
      periodChanged,
  );
}
