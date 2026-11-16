/** Cliente do bounded context Produtos — exclusivamente os contratos
 * E-PRD da Engineering API (/v1/products*). O MFE nunca chama api-delpi
 * nem decide autorização; erros chegam já classificados pelo httpClient
 * e 404 vira estado "não encontrado" honesto na UI. */

import { getBlob, getJson, postJson, HomeApiError } from "../../../api/httpClient";
import type {
  LineBalanceRequest,
  ProductDetailResult,
  ProductDrawingMetadata,
  ProductFilterOptions,
  ProductListResult,
  ProductLineBalanceResult,
  ProductParentsResult,
  ProductRoutingResult,
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

/* --- Roteiro oficial + balanceamento (Doc 126) ----------------------- */

const ROUTING_PAGE_SIZE = 500;
/** Teto de segurança da paginação agregada — acima disso a resposta é
 * reportada como parcial em vez de truncar silenciosamente. */
const ROUTING_MAX_PAGES = 20;

/** Roteiro oficial completo do produto — o owner pagina o payload e a
 * primeira página NÃO representa o roteiro inteiro; aqui as páginas são
 * agregadas até `total` (ou o teto de segurança). `branch` é filtro do
 * contrato oficial — nunca filtrar filial no cliente após mesclar. */
export async function fetchProductRouting(
  code: string,
  options: { branch?: string } = {},
  signal?: AbortSignal,
): Promise<ProductRoutingResult & { truncated?: boolean }> {
  const base = `${BASE}/${encodeURIComponent(code)}/routing`;
  const pageParams = (page: number) => {
    const p = new URLSearchParams();
    if (options.branch) p.set("branch", options.branch);
    p.set("page", String(page));
    p.set("page_size", String(ROUTING_PAGE_SIZE));
    return p.toString();
  };
  const first = await getJson<Envelope<ProductRoutingResult>>(
    `${base}?${pageParams(1)}`,
    signal,
  );
  const data = first.data;
  const items = Array.isArray(data?.items) ? [...data.items] : [];
  const total = typeof data?.total === "number" ? data.total : items.length;
  let page = 1;
  let truncated = false;
  while (items.length < total) {
    if (page >= ROUTING_MAX_PAGES) {
      truncated = true;
      break;
    }
    page += 1;
    const next = await getJson<Envelope<ProductRoutingResult>>(
      `${base}?${pageParams(page)}`,
      signal,
    );
    const more = Array.isArray(next.data?.items) ? next.data.items : [];
    if (!more.length) {
      truncated = items.length < total;
      break;
    }
    items.push(...more);
  }
  return { ...data, items, total, truncated };
}

/** Análise determinística de balanceamento — POST ao BFF que executa o
 * domínio EVA (`build_balance_result`); o MFE envia somente o
 * vocabulário fechado do contrato e renderiza o resultado sem
 * recalcular. */
export async function postProductLineBalance(
  code: string,
  params: LineBalanceRequest,
  signal?: AbortSignal,
): Promise<ProductLineBalanceResult> {
  const res = await postJson<Envelope<ProductLineBalanceResult>>(
    `${BASE}/${encodeURIComponent(code)}/line-balance`,
    params,
    signal,
  );
  return res.data;
}
