import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type { ProductStructureData, ProductSummaryData } from "../types/production";

export const PRODUCT_API_BASE = "/apps/api-delpi/products";

async function fetchProductData<T>(
  path: string,
  signal?: AbortSignal
): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${PRODUCT_API_BASE}${path}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro na API de produtos");
}

export function getProductSummary(code: string, signal?: AbortSignal) {
  const encoded = encodeURIComponent(code.trim());
  return fetchProductData<ProductSummaryData>(`/${encoded}/summary`, signal);
}

export function getProductDetail(
  code: string,
  view: "summary" | "full" = "summary",
  signal?: AbortSignal
) {
  const encoded = encodeURIComponent(code.trim());
  const query = view === "summary" ? "?view=summary" : "";
  return fetchProductData<{ product: Record<string, unknown> }>(
    `/${encoded}${query}`,
    signal
  );
}

export function getProductStructure(code: string, signal?: AbortSignal) {
  const encoded = encodeURIComponent(code.trim());
  return fetchProductData<ProductStructureData>(
    `/${encoded}/structure?page_size=200`,
    signal
  );
}
