import type { PurchaseRequestsQuery } from "../types/purchaseRequests";

function appendTrimmed(params: URLSearchParams, key: string, values: readonly string[] | undefined): void {
  for (const value of values ?? []) {
    const trimmed = value.trim();
    if (trimmed) params.append(key, trimmed);
  }
}

export function buildListSearchParams(
  query: Partial<PurchaseRequestsQuery> & { branch?: string },
): URLSearchParams {
  const params = new URLSearchParams();

  if (query.branch) params.set("branch", query.branch.trim());
  if (query.date_from?.trim()) params.set("date_from", query.date_from.trim());
  if (query.date_to?.trim()) params.set("date_to", query.date_to.trim());
  if (query.request_number?.trim()) params.set("request_number", query.request_number.trim());
  appendTrimmed(params, "requester_user_id", query.requester_user_ids);
  appendTrimmed(params, "cost_center", query.cost_center_codes);
  if (query.product_code?.trim()) params.set("product_code", query.product_code.trim());
  if (query.supplier_code?.trim()) params.set("supplier_code", query.supplier_code.trim());
  if (query.order_number?.trim()) params.set("order_number", query.order_number.trim());
  appendTrimmed(params, "overall_stage", query.overall_stages);
  if (query.page && query.page > 0) params.set("page", String(query.page));
  if (query.page_size && query.page_size > 0) params.set("page_size", String(query.page_size));

  return params;
}

/** @deprecated Use buildListSearchParams — mantido para chamadas legadas pontuais. */
export function buildListQueryParams(
  query: Partial<PurchaseRequestsQuery> & { branch?: string },
): Record<string, string> {
  const params = buildListSearchParams(query);
  const record: Record<string, string> = {};
  params.forEach((value, key) => {
    record[key] = value;
  });
  return record;
}
