import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  SellerCustomerInput,
  SellerPortfolio,
  SellerPortfolioMeResponse,
} from "../types/sellerPortfolio";
import { httpDelete, httpGet, httpPatch, httpPost, httpPut } from "./httpClient";
import { PEDIDOS_VENDA_ABERTOS_API_BASE } from "./pedidosVendaAbertosApi";

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};

type DirectorySearchResponse = {
  items?: DirectoryUser[];
};

export async function searchDirectoryUsers(
  query: string,
  limit = 10,
  signal?: AbortSignal,
): Promise<DirectoryUser[]> {
  const normalized = query.trim();
  if (normalized.length < 2) return [];

  const params = new URLSearchParams({
    q: normalized,
    limit: String(limit),
    include_self: "true",
  });

  const payload = await httpGet<DirectorySearchResponse>(
    `/core-api/me/directory/users?${params.toString()}`,
    { signal },
  );
  return payload.items ?? [];
}

export async function getMySellerPortfolio(
  signal?: AbortSignal,
): Promise<SellerPortfolioMeResponse> {
  const response = await httpGet<ApiSuccessResponse<SellerPortfolioMeResponse>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/sellers/me`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar carteira do usuário.");
}

export async function listSellerPortfolios(
  options?: { activeOnly?: boolean; signal?: AbortSignal },
): Promise<SellerPortfolio[]> {
  const params = new URLSearchParams();
  if (options?.activeOnly) params.set("active_only", "true");
  const qs = params.toString();
  const response = await httpGet<ApiSuccessResponse<{ items: SellerPortfolio[] }>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/sellers${qs ? `?${qs}` : ""}`,
    { signal: options?.signal },
  );
  const data = unwrapApiDelpiEnvelope(response, "Erro ao listar vendedores.");
  return data.items ?? [];
}

export async function createSellerPortfolio(input: {
  user_id: string;
  display_name: string;
  customers?: SellerCustomerInput[];
}): Promise<SellerPortfolio> {
  const response = await httpPost<ApiSuccessResponse<SellerPortfolio>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/sellers`,
    input,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao cadastrar vendedor.");
}

export async function updateSellerPortfolio(
  sellerId: string,
  input: { display_name?: string; active?: boolean },
): Promise<SellerPortfolio> {
  const response = await httpPatch<ApiSuccessResponse<SellerPortfolio>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/sellers/${encodeURIComponent(sellerId)}`,
    input,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao atualizar vendedor.");
}

export async function deactivateSellerPortfolio(sellerId: string): Promise<SellerPortfolio> {
  const response = await httpDelete<ApiSuccessResponse<SellerPortfolio>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/sellers/${encodeURIComponent(sellerId)}`,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao desativar vendedor.");
}

export async function replaceSellerCustomers(
  sellerId: string,
  customers: SellerCustomerInput[],
): Promise<SellerPortfolio> {
  const response = await httpPut<ApiSuccessResponse<SellerPortfolio>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/sellers/${encodeURIComponent(sellerId)}/customers`,
    { customers },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao atualizar clientes da carteira.");
}

export async function addSellerCustomer(
  sellerId: string,
  customer: SellerCustomerInput,
): Promise<SellerPortfolio> {
  const response = await httpPost<ApiSuccessResponse<SellerPortfolio>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/sellers/${encodeURIComponent(sellerId)}/customers`,
    customer,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao adicionar cliente.");
}

export async function removeSellerCustomer(
  sellerId: string,
  customerCode: string,
  customerStore: string,
): Promise<SellerPortfolio> {
  const params = new URLSearchParams({
    customer_code: customerCode,
    customer_store: customerStore,
  });
  const response = await httpDelete<ApiSuccessResponse<SellerPortfolio>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/sellers/${encodeURIComponent(sellerId)}/customers?${params}`,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao remover cliente.");
}

export type TransferSellerCustomersResult = {
  source: SellerPortfolio;
  target: SellerPortfolio;
  transferred_count: number;
};

export async function transferSellerCustomers(
  sourceSellerId: string,
  input: {
    target_seller_id: string;
    customers: SellerCustomerInput[];
  },
): Promise<TransferSellerCustomersResult> {
  const response = await httpPost<ApiSuccessResponse<TransferSellerCustomersResult>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/sellers/${encodeURIComponent(sourceSellerId)}/customers/transfer`,
    input,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao transferir clientes.");
}

export type TotvsCustomerHit = {
  code: string;
  store: string;
  name: string;
  blocked?: string | null;
};

type TotvsCustomerPage = {
  items?: Array<{
    code?: string | null;
    store?: string | null;
    name?: string | null;
    blocked?: string | null;
  }>;
  page?: number;
  page_size?: number;
  total?: number;
  total_pages?: number;
};

/** Clientes ativos SA1 (TOTVS) para amarração na config de carteira. */
export async function searchActiveTotvsCustomers(
  query: string,
  options?: { page?: number; pageSize?: number; signal?: AbortSignal },
): Promise<{ items: TotvsCustomerHit[]; total: number }> {
  const params = new URLSearchParams({
    page: String(options?.page ?? 1),
    page_size: String(options?.pageSize ?? 15),
  });
  const normalized = query.trim();
  if (normalized) params.set("q", normalized);

  const response = await httpGet<ApiSuccessResponse<TotvsCustomerPage>>(
    `${PEDIDOS_VENDA_ABERTOS_API_BASE}/customers/search?${params.toString()}`,
    { signal: options?.signal },
  );
  const data = unwrapApiDelpiEnvelope(response, "Erro ao buscar clientes no TOTVS.");
  return {
    items: (data.items ?? []).map((row) => ({
      code: (row.code ?? "").trim(),
      store: (row.store ?? "").trim(),
      name: (row.name ?? "").trim(),
      blocked: row.blocked ?? null,
    })),
    total: data.total ?? 0,
  };
}
