/** Cliente do bounded context Produtos — exclusivamente os contratos
 * E-PRD da Engineering API (/v1/products*). O MFE nunca chama api-delpi
 * nem decide autorização; erros chegam já classificados pelo httpClient
 * e 404 vira estado "não encontrado" honesto na UI. */

import { getBlob, getJson, HomeApiError } from "../../../api/httpClient";
import type {
  ProductDetailResult,
  ProductDrawingMetadata,
  ProductFilterOptions,
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
  return requireItems(res.data);
}

export async function fetchProductFilterOptions(
  signal?: AbortSignal,
): Promise<ProductFilterOptions> {
  const res = await getJson<Envelope<ProductFilterOptions>>(
    `${BASE}/filter-options`,
    signal,
  );
  const data = res.data;
  return {
    groups: Array.isArray(data?.groups) ? data.groups : [],
    types: Array.isArray(data?.types) ? data.types : [],
  };
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

/** Envelope delegado legado da rota `/structure` (contrato LMP.G5):
 * `data` vem como `{status, data: payload}` — os demais endpoints já
 * chegam planos via `_delegated`. Desempacota e classifica os estados
 * honestos em vez de deixar o componente ler `items` de um wrapper. */
type DelegatedEnvelope<T> = {
  status?: string;
  data?: T;
};

function unwrapDelegated<T>(payload: T | DelegatedEnvelope<T>): T {
  const wrapped = payload as DelegatedEnvelope<T>;
  if (wrapped && typeof wrapped === "object" && "status" in wrapped) {
    if (wrapped.status === "available") {
      return wrapped.data as T;
    }
    if (wrapped.status === "forbidden") {
      throw new HomeApiError(
        "forbidden",
        "Acesso negado pela fonte oficial de produtos.",
        403,
      );
    }
    if (wrapped.status === "not_found") {
      throw new HomeApiError(
        "unavailable",
        "Produto não encontrado na fonte oficial.",
        404,
      );
    }
    throw new HomeApiError(
      "unavailable",
      "Fonte de produtos indisponível no momento.",
      502,
    );
  }
  return payload as T;
}

function requireItems<T extends { items: unknown }>(result: T): T {
  if (!Array.isArray(result?.items)) {
    throw new HomeApiError(
      "contract_error",
      "Resposta da fonte oficial sem lista de itens válida.",
    );
  }
  return result;
}

export async function fetchProductStructure(
  code: string,
  signal?: AbortSignal,
): Promise<ProductStructureResult> {
  const res = await getJson<
    Envelope<ProductStructureResult | DelegatedEnvelope<ProductStructureResult>>
  >(`${BASE}/${encodeURIComponent(code)}/structure`, signal);
  return requireItems(unwrapDelegated(res.data));
}

export async function fetchProductParents(
  code: string,
  signal?: AbortSignal,
): Promise<ProductParentsResult> {
  const res = await getJson<Envelope<ProductParentsResult>>(
    `${BASE}/${encodeURIComponent(code)}/parents`,
    signal,
  );
  return requireItems(res.data);
}

export async function fetchProductSuppliers(
  code: string,
  signal?: AbortSignal,
): Promise<ProductSuppliersResult> {
  const res = await getJson<Envelope<ProductSuppliersResult>>(
    `${BASE}/${encodeURIComponent(code)}/suppliers`,
    signal,
  );
  return requireItems(res.data);
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
