import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  SafetyStockFiltersData,
  SafetyStockItemDetails,
  SafetyStockItemsData,
  SafetyStockLinkedSuppliersData,
  SafetyStockQueryParams,
  SafetyStockSummaryData,
  SafetyStockSupplierPriceHistoryData,
} from "../types/safetyStock";
import { queryString } from "../utils/queryParams";

const API_BASE = "/apps/api-delpi/supplies/safety-stock";

type RequestOptions = { signal?: AbortSignal };

async function getEnvelope<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const payload = await httpGet<unknown>(`${API_BASE}${path}`, options);
  return unwrapApiDelpiEnvelope<T>(payload);
}

function sharedQuery(params: Pick<
  SafetyStockQueryParams,
  | "branch"
  | "includeBlocked"
  | "productGroup"
  | "unit"
  | "search"
  | "status"
  | "includeWithoutSafetyStock"
>) {
  return {
    branch: params.branch,
    includeBlocked: params.includeBlocked,
    productGroup: params.productGroup || undefined,
    unit: params.unit || undefined,
    search: params.search || undefined,
    status: params.status || undefined,
    includeWithoutSafetyStock: params.includeWithoutSafetyStock,
  };
}

export async function fetchSafetyStockFilters(
  branch: string,
  includeBlocked: boolean,
  options: RequestOptions = {},
): Promise<SafetyStockFiltersData> {
  return getEnvelope<SafetyStockFiltersData>(
    `/filters${queryString({ branch, includeBlocked })}`,
    options,
  );
}

export async function fetchSafetyStockSummary(
  params: SafetyStockQueryParams,
  options: RequestOptions = {},
): Promise<SafetyStockSummaryData> {
  return getEnvelope<SafetyStockSummaryData>(
    `/summary${queryString(sharedQuery(params))}`,
    options,
  );
}

export async function fetchSafetyStockItems(
  params: SafetyStockQueryParams,
  page: number,
  pageSize: number,
  options: RequestOptions = {},
): Promise<SafetyStockItemsData> {
  return getEnvelope<SafetyStockItemsData>(
    `/items${queryString({
      ...sharedQuery(params),
      page,
      pageSize,
      sortBy: params.sortBy,
      sortDirection: params.sortDirection,
    })}`,
    options,
  );
}

export async function fetchSafetyStockItemDetails(
  branch: string,
  productCode: string,
  options: RequestOptions = {},
): Promise<SafetyStockItemDetails> {
  const encoded = encodeURIComponent(productCode.trim());
  return getEnvelope<SafetyStockItemDetails>(
    `/items/${encoded}/details${queryString({ branch })}`,
    options,
  );
}

export async function fetchSafetyStockItemSuppliers(
  branch: string,
  productCode: string,
  options: RequestOptions = {},
): Promise<SafetyStockLinkedSuppliersData> {
  const encoded = encodeURIComponent(productCode.trim());
  return getEnvelope<SafetyStockLinkedSuppliersData>(
    `/items/${encoded}/suppliers${queryString({ branch })}`,
    options,
  );
}

export async function fetchSafetyStockSupplierPriceHistory(
  branch: string,
  productCode: string,
  supplierCode: string,
  supplierStore: string,
  options: RequestOptions = {},
): Promise<SafetyStockSupplierPriceHistoryData> {
  const encodedProduct = encodeURIComponent(productCode.trim());
  const encodedSupplier = encodeURIComponent(supplierCode.trim());
  return getEnvelope<SafetyStockSupplierPriceHistoryData>(
    `/items/${encodedProduct}/suppliers/${encodedSupplier}/purchase-price-history${queryString({
      branch,
      supplierStore: supplierStore.trim(),
    })}`,
    options,
  );
}

/** Descobre filial autorizada tentando candidatos na ordem do backend. */
export async function bootstrapSafetyStockFilters(
  includeBlocked: boolean,
  options: RequestOptions = {},
): Promise<SafetyStockFiltersData> {
  const candidates = ["01", "02"];
  let lastError: unknown;

  for (const branch of candidates) {
    try {
      return await fetchSafetyStockFilters(branch, includeBlocked, options);
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError;
}
