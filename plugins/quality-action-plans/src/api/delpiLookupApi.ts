import { httpGet, unwrapApiDelpiEnvelope, type ApiEnvelope } from "./httpClient";

const PRODUCTS_BASE = "/apps/api-delpi/products";
const CUSTOMERS_BASE = "/apps/api-delpi/customers";

type PagedLookupResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

export type DelpiProductLookupItem = {
  code: string;
  description: string;
};

export type DelpiCustomerLookupItem = {
  code: string;
  store: string;
  name: string;
};

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value == null || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

async function fetchPaged<T>(
  url: string,
  fallbackMessage: string,
  signal?: AbortSignal,
): Promise<PagedLookupResponse<T>> {
  const envelope = await httpGet<ApiEnvelope<PagedLookupResponse<T>>>(url, { signal });
  return unwrapApiDelpiEnvelope(envelope, fallbackMessage);
}

export async function searchDelpiProducts(params: {
  code?: string;
  description?: string;
  pageSize?: number;
  signal?: AbortSignal;
}): Promise<DelpiProductLookupItem[]> {
  const query = buildQuery({
    code: params.code?.trim(),
    description: params.description?.trim(),
    page: 1,
    page_size: params.pageSize ?? 15,
  });
  const data = await fetchPaged<Record<string, unknown>>(
    `${PRODUCTS_BASE}/search${query}`,
    "Erro ao buscar produtos na api-delpi.",
    params.signal,
  );
  return data.items
    .map((item) => ({
      code: String(item.code ?? "").trim(),
      description: String(item.description ?? "").trim(),
    }))
    .filter((item) => item.code);
}

export async function fetchDelpiProductSummary(
  code: string,
  signal?: AbortSignal,
): Promise<DelpiProductLookupItem | null> {
  const normalized = code.trim();
  if (!normalized) return null;
  const envelope = await httpGet<ApiEnvelope<Record<string, unknown>>>(
    `${PRODUCTS_BASE}/${encodeURIComponent(normalized)}?view=summary`,
    { signal },
  );
  const data = unwrapApiDelpiEnvelope(envelope, "Erro ao carregar produto.");
  const productCode = String(data.code ?? normalized).trim();
  if (!productCode) return null;
  return {
    code: productCode,
    description: String(data.description ?? "").trim(),
  };
}

export async function searchDelpiCustomers(params: {
  code?: string;
  name?: string;
  store?: string;
  pageSize?: number;
  signal?: AbortSignal;
}): Promise<DelpiCustomerLookupItem[]> {
  const query = buildQuery({
    code: params.code?.trim(),
    name: params.name?.trim(),
    store: params.store?.trim(),
    page: 1,
    page_size: params.pageSize ?? 15,
  });
  const data = await fetchPaged<Record<string, unknown>>(
    `${CUSTOMERS_BASE}/search${query}`,
    "Erro ao buscar clientes na api-delpi.",
    params.signal,
  );
  return data.items
    .map((item) => ({
      code: String(item.code ?? "").trim(),
      store: String(item.store ?? "").trim(),
      name: String(item.name ?? "").trim(),
    }))
    .filter((item) => item.code);
}
