import { httpGet } from "./httpClient";
import {
  unwrapApiDelpiEnvelope,
  type ApiSuccessResponse,
} from "../types/lmp";
import type { ProductStructureData } from "../types/productStructure";

const PRODUCT_API_BASE = "/apps/api-delpi/products";

export type ProductSearchItem = {
  code: string;
  description: string;
};

type ProductSearchPage = {
  items: Array<Record<string, unknown>>;
  total?: number;
  page?: number;
  page_size?: number;
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

function mapProductItem(item: Record<string, unknown>): ProductSearchItem | null {
  const code = String(item.code ?? "").trim();
  if (!code) return null;
  return {
    code,
    description: String(item.description ?? "").trim(),
  };
}

/** Heurística: código Protheus vs texto de descrição. */
export function looksLikeProductCodeQuery(query: string): boolean {
  const trimmed = query.trim();
  if (!trimmed) return false;
  if (/^9026/i.test(trimmed)) return true;
  return /^[0-9A-Za-z./-]+$/.test(trimmed) && !/\s/.test(trimmed);
}

export async function searchProducts(
  query: string,
  signal?: AbortSignal,
): Promise<ProductSearchItem[]> {
  const trimmed = query.trim();
  if (trimmed.length < 2) return [];
  const params = looksLikeProductCodeQuery(trimmed)
    ? { code: trimmed, page: 1, page_size: 20 }
    : { description: trimmed, page: 1, page_size: 20 };
  const response = await httpGet<ApiSuccessResponse<ProductSearchPage>>(
    `${PRODUCT_API_BASE}/search${buildQuery(params)}`,
    { signal },
  );
  const data = unwrapApiDelpiEnvelope(response, "Erro ao buscar produtos");
  return (data.items ?? [])
    .map((item) => mapProductItem(item))
    .filter((item): item is ProductSearchItem => item !== null);
}

export async function getProductStructure(
  code: string,
  signal?: AbortSignal
): Promise<ProductStructureData> {
  const encoded = encodeURIComponent(code.trim());
  const response = await httpGet<ApiSuccessResponse<ProductStructureData>>(
    `${PRODUCT_API_BASE}/${encoded}/structure?max_depth=6&page_size=200`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar estrutura do produto");
}
