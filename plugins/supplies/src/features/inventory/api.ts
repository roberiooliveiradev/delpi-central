import { httpGet, suppliesApiUrl } from "../../api/httpClient";
import type {
  InventoryItemsResponse,
  InventoryQuery,
  InventorySummaryResponse,
} from "./types";
import { buildItemsSearchParams, buildSummarySearchParams } from "./query";

export async function getInventoryStockBalancesSummary(
  query: Pick<InventoryQuery, "branches" | "warehouse">,
  signal?: AbortSignal,
  options?: { includeWarehouse?: boolean },
): Promise<InventorySummaryResponse> {
  const qs = buildSummarySearchParams(query, options).toString();
  return httpGet<InventorySummaryResponse>(
    suppliesApiUrl(
      qs
        ? `/inventory/stock-balances/summary?${qs}`
        : `/inventory/stock-balances/summary`,
    ),
    { signal },
  );
}

export async function listInventoryStockBalances(
  query: InventoryQuery,
  signal?: AbortSignal,
): Promise<InventoryItemsResponse> {
  const qs = buildItemsSearchParams(query).toString();
  return httpGet<InventoryItemsResponse>(
    suppliesApiUrl(`/inventory/stock-balances/items?${qs}`),
    { signal },
  );
}
