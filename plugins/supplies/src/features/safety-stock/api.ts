import { httpGet, suppliesApiUrl } from "../../api/httpClient";
import { SAFETY_STOCK_CONTENT as C } from "./content";
import { buildItemsSearchParams, buildScopeFilterParams } from "./query";
import type {
  SafetyStockDetailTarget,
  SafetyStockFiltersResponse,
  SafetyStockItemDetail,
  SafetyStockItemsResponse,
  SafetyStockQuery,
  SafetyStockSummary,
  SafetyStockSuppliersResponse,
} from "./types";

/**
 * Resposta HTTP 200 com payload malformado NÃO é empty-state legítimo
 * (residual de envelope apontado na revisão de E11.S1): o guard transforma
 * shape inválido em erro de integração explícito.
 */
export class SafetyStockContractError extends Error {
  constructor() {
    super(C.invalidResponse);
    this.name = "SafetyStockContractError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function isSafetyStockSummary(value: unknown): value is SafetyStockSummary {
  if (!isRecord(value)) return false;
  return (
    typeof value.total_materials === "number" &&
    typeof value.with_safety_stock === "number" &&
    typeof value.without_safety_stock === "number" &&
    typeof value.below_safety_stock === "number" &&
    typeof value.at_safety_stock === "number" &&
    typeof value.above_safety_stock === "number" &&
    typeof value.with_primary_stock === "number" &&
    typeof value.without_primary_stock === "number" &&
    typeof value.with_work_in_process_stock === "number" &&
    Array.isArray(value.deficit_by_unit)
  );
}

export function isSafetyStockItemsResponse(
  value: unknown,
): value is SafetyStockItemsResponse {
  if (!isRecord(value)) return false;
  return (
    Array.isArray(value.items) &&
    typeof value.total === "number" &&
    typeof value.page === "number"
  );
}

export function isSafetyStockFiltersResponse(
  value: unknown,
): value is SafetyStockFiltersResponse {
  if (!isRecord(value)) return false;
  return (
    Array.isArray(value.branch_catalog) &&
    Array.isArray(value.product_groups) &&
    Array.isArray(value.units)
  );
}

export async function getSafetyStockFilters(
  branch: string,
  includeBlocked: boolean,
  signal?: AbortSignal,
): Promise<SafetyStockFiltersResponse> {
  const params = new URLSearchParams();
  params.set("branch", branch);
  params.set("includeBlocked", includeBlocked ? "true" : "false");
  const payload = await httpGet<unknown>(
    suppliesApiUrl(`/safety-stock/filters?${params.toString()}`),
    { signal },
  );
  if (!isSafetyStockFiltersResponse(payload)) throw new SafetyStockContractError();
  return payload;
}

export async function getSafetyStockSummary(
  query: SafetyStockQuery,
  signal?: AbortSignal,
): Promise<SafetyStockSummary> {
  const params = buildScopeFilterParams(query);
  const payload = await httpGet<unknown>(
    suppliesApiUrl(`/safety-stock/summary?${params.toString()}`),
    { signal },
  );
  if (!isSafetyStockSummary(payload)) throw new SafetyStockContractError();
  return payload;
}

export async function listSafetyStockItems(
  query: SafetyStockQuery,
  signal?: AbortSignal,
): Promise<SafetyStockItemsResponse> {
  const params = buildItemsSearchParams(query);
  const payload = await httpGet<unknown>(
    suppliesApiUrl(`/safety-stock/items?${params.toString()}`),
    { signal },
  );
  if (!isSafetyStockItemsResponse(payload)) throw new SafetyStockContractError();
  return payload;
}

/* E11.S3 — detalhe do item e fornecedores (filial concreta obrigatória). */

export function isSafetyStockItemDetail(
  value: unknown,
): value is SafetyStockItemDetail {
  if (!isRecord(value)) return false;
  const product = value.product;
  const stock = value.stock;
  if (!isRecord(product) || !isRecord(stock)) return false;
  if (typeof product.product_code !== "string" || !product.product_code.trim()) {
    return false;
  }
  return typeof product.branch === "string" && Boolean(product.branch.trim());
}

export function isSafetyStockSuppliersResponse(
  value: unknown,
): value is SafetyStockSuppliersResponse {
  if (!isRecord(value)) return false;
  return Array.isArray(value.items) && typeof value.total === "number";
}

export async function getSafetyStockItemDetails(
  target: SafetyStockDetailTarget,
  signal?: AbortSignal,
): Promise<SafetyStockItemDetail> {
  const params = new URLSearchParams();
  params.set("branch", target.branch);
  const payload = await httpGet<unknown>(
    suppliesApiUrl(
      `/safety-stock/items/${encodeURIComponent(target.productCode)}/details?${params.toString()}`,
    ),
    { signal },
  );
  if (!isSafetyStockItemDetail(payload)) throw new SafetyStockContractError();
  return payload;
}

export async function getSafetyStockItemSuppliers(
  target: SafetyStockDetailTarget,
  signal?: AbortSignal,
): Promise<SafetyStockSuppliersResponse> {
  const params = new URLSearchParams();
  params.set("branch", target.branch);
  const payload = await httpGet<unknown>(
    suppliesApiUrl(
      `/safety-stock/items/${encodeURIComponent(target.productCode)}/suppliers?${params.toString()}`,
    ),
    { signal },
  );
  if (!isSafetyStockSuppliersResponse(payload)) {
    throw new SafetyStockContractError();
  }
  return payload;
}
