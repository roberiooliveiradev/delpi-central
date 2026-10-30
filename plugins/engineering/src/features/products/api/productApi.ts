/** Cliente do bounded context Produtos — exclusivamente os contratos
 * E-PRD da Engineering API (/v1/products*). O MFE nunca chama api-delpi
 * nem decide autorização; erros chegam já classificados pelo httpClient
 * e 404 vira estado "não encontrado" honesto na UI. */

import { getBlob, getJson } from "../../../api/httpClient";
import type {
  ProductDetailResult,
  ProductDrawingMetadata,
  ProductListResult,
  ProductParentsResult,
  ProductStructureResult,
  ProductSuppliersResult,
} from "../types";

const BASE = "/apps/engineering-api/v1/products";

type Envelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export type ProductSearchFilters = {
  code?: string;
  description?: string;
  group_code?: string;
  subgroup?: string;
  product_type?: string;
  customer_reference?: string;
  sort?: string;
  direction?: string;
  page?: number;
  page_size?: number;
};

function qs(filters: ProductSearchFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") continue;
    params.set(key, String(value));
  }
  const text = params.toString();
  return text ? `?${text}` : "";
}

export async function searchProducts(
  filters: ProductSearchFilters,
  signal?: AbortSignal,
): Promise<ProductListResult> {
  const res = await getJson<Envelope<ProductListResult>>(
    `${BASE}${qs(filters)}`,
    signal,
  );
  return res.data;
}

export async function fetchProductDetail(
  code: string,
  signal?: AbortSignal,
): Promise<ProductDetailResult> {
  const res = await getJson<Envelope<ProductDetailResult>>(
    `${BASE}/${encodeURIComponent(code)}`,
    signal,
  );
  return res.data;
}

export async function fetchProductStructure(
  code: string,
  signal?: AbortSignal,
): Promise<ProductStructureResult> {
  const res = await getJson<Envelope<ProductStructureResult>>(
    `${BASE}/${encodeURIComponent(code)}/structure`,
    signal,
  );
  return res.data;
}

export async function fetchProductParents(
  code: string,
  signal?: AbortSignal,
): Promise<ProductParentsResult> {
  const res = await getJson<Envelope<ProductParentsResult>>(
    `${BASE}/${encodeURIComponent(code)}/parents`,
    signal,
  );
  return res.data;
}

export async function fetchProductSuppliers(
  code: string,
  signal?: AbortSignal,
): Promise<ProductSuppliersResult> {
  const res = await getJson<Envelope<ProductSuppliersResult>>(
    `${BASE}/${encodeURIComponent(code)}/suppliers`,
    signal,
  );
  return res.data;
}

export async function fetchProductDrawing(
  code: string,
  signal?: AbortSignal,
): Promise<ProductDrawingMetadata> {
  const res = await getJson<Envelope<ProductDrawingMetadata>>(
    `${BASE}/${encodeURIComponent(code)}/drawing`,
    signal,
  );
  return res.data;
}

export async function fetchProductDrawingPdf(
  code: string,
  signal?: AbortSignal,
): Promise<Blob> {
  return getBlob(
    `${BASE}/${encodeURIComponent(code)}/drawing/pdf`,
    signal,
  );
}

export async function fetchProductHistory(
  code: string,
  signal?: AbortSignal,
): Promise<Record<string, unknown>> {
  const res = await getJson<Envelope<Record<string, unknown>>>(
    `${BASE}/${encodeURIComponent(code)}/purchase-price-history`,
    signal,
  );
  return res.data;
}
