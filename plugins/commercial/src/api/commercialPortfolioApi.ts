import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  CustomerEnrichmentItem,
  DirectoryUser,
  SellerCustomerInput,
  SellerPortfolio,
  SellerPortfolioMeResponse,
  TotvsCustomerHit,
  TransferSellerCustomersResult,
} from "../types/portfolio";
import {
  commercialApiUrl,
  httpDelete,
  httpGet,
  httpGetBlob,
  httpPatch,
  httpPost,
  httpPut,
  httpPutFormData,
} from "./httpClient";

export async function getMySellerPortfolio(signal?: AbortSignal): Promise<SellerPortfolioMeResponse> {
  const response = await httpGet<ApiSuccessResponse<SellerPortfolioMeResponse>>(
    commercialApiUrl("/seller-portfolios/me"),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar carteira do usuário.");
}

export async function listSellerPortfolios(
  options?: { activeOnly?: boolean; signal?: AbortSignal },
): Promise<SellerPortfolio[]> {
  const params = new URLSearchParams();
  if (options?.activeOnly) params.set("active_only", "true");
  const qs = params.toString();
  const response = await httpGet<ApiSuccessResponse<{ items: SellerPortfolio[] }>>(
    `${commercialApiUrl("/seller-portfolios")}/${qs ? `?${qs}` : ""}`,
    { signal: options?.signal },
  );
  const data = unwrapEnvelope(response, "Erro ao listar carteiras.");
  return data.items ?? [];
}

export async function createSellerPortfolio(input: {
  user_id: string;
  display_name: string;
  customers?: SellerCustomerInput[];
}): Promise<SellerPortfolio> {
  const response = await httpPost<ApiSuccessResponse<SellerPortfolio>>(
    commercialApiUrl("/seller-portfolios/"),
    input,
  );
  return unwrapEnvelope(response, "Erro ao cadastrar vendedor.");
}

export async function transferSellerCustomers(input: {
  source_portfolio_id: string;
  target_portfolio_id: string;
  customers: SellerCustomerInput[];
  reason_note: string;
}): Promise<TransferSellerCustomersResult> {
  const response = await httpPost<ApiSuccessResponse<TransferSellerCustomersResult>>(
    commercialApiUrl("/seller-portfolios/transfer"),
    input,
  );
  return unwrapEnvelope(response, "Erro ao transferir clientes.");
}

export async function addSellerCustomer(
  portfolioId: string,
  customer: SellerCustomerInput,
): Promise<SellerPortfolio> {
  const response = await httpPost<ApiSuccessResponse<SellerPortfolio>>(
    commercialApiUrl(`/seller-portfolios/${encodeURIComponent(portfolioId)}/customers`),
    customer,
  );
  return unwrapEnvelope(response, "Erro ao adicionar cliente à carteira.");
}

export async function removeSellerCustomer(
  portfolioId: string,
  customerCode: string,
  customerStore: string,
): Promise<SellerPortfolio> {
  const response = await httpDelete<ApiSuccessResponse<SellerPortfolio>>(
    commercialApiUrl(
      `/seller-portfolios/${encodeURIComponent(portfolioId)}/customers/${encodeURIComponent(
        customerCode,
      )}/${encodeURIComponent(customerStore)}`,
    ),
  );
  return unwrapEnvelope(response, "Erro ao remover cliente da carteira.");
}

export async function replaceSellerCustomers(
  portfolioId: string,
  customers: SellerCustomerInput[],
): Promise<SellerPortfolio> {
  const response = await httpPut<ApiSuccessResponse<SellerPortfolio>>(
    commercialApiUrl(`/seller-portfolios/${encodeURIComponent(portfolioId)}/customers`),
    { customers },
  );
  return unwrapEnvelope(response, "Erro ao atualizar clientes da carteira.");
}

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

  const payload = await httpGet<{ items?: DirectoryUser[] }>(
    `/core-api/me/directory/users?${params.toString()}`,
    { signal },
  );
  return payload.items ?? [];
}

export async function searchActiveCustomers(
  query: string,
  options?: { page?: number; pageSize?: number; signal?: AbortSignal },
): Promise<{ items: TotvsCustomerHit[]; total: number }> {
  const params = new URLSearchParams({
    page: String(options?.page ?? 1),
    page_size: String(options?.pageSize ?? 15),
  });
  const normalized = query.trim();
  if (normalized) params.set("q", normalized);

  const response = await httpGet<
    ApiSuccessResponse<{
      items?: Array<{
        code?: string | null;
        store?: string | null;
        name?: string | null;
        blocked?: string | null;
      }>;
      total?: number;
    }>
  >(`${commercialApiUrl("/customers/search")}?${params.toString()}`, {
    signal: options?.signal,
  });
  const data = unwrapEnvelope(response, "Erro ao buscar clientes.");
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

export async function enrichPortfolioCustomers(
  customers: Array<{ customer_code: string; customer_store: string }>,
  signal?: AbortSignal,
): Promise<CustomerEnrichmentItem[]> {
  if (customers.length === 0) return [];
  const response = await httpPost<ApiSuccessResponse<{ items?: CustomerEnrichmentItem[] }>>(
    commercialApiUrl("/customers/enrichment"),
    { customers },
    { signal },
  );
  const data = unwrapEnvelope(response, "Erro ao enriquecer clientes.");
  return data.items ?? [];
}

export function customerAvatarUrl(code: string, store: string): string {
  return commercialApiUrl(
    `/customers/${encodeURIComponent(code)}/${encodeURIComponent(store)}/avatar`,
  );
}

export async function fetchCustomerAvatarObjectUrl(
  code: string,
  store: string,
  signal?: AbortSignal,
): Promise<string | null> {
  try {
    const blob = await httpGetBlob(customerAvatarUrl(code, store), { signal });
    return URL.createObjectURL(blob);
  } catch {
    return null;
  }
}

export async function upsertCustomerAvatar(code: string, store: string, file: File): Promise<void> {
  const form = new FormData();
  form.append("file", file);
  const response = await httpPutFormData<ApiSuccessResponse<Record<string, unknown>>>(
    customerAvatarUrl(code, store),
    form,
  );
  unwrapEnvelope(response, "Erro ao salvar logo do cliente.");
}

export async function deleteCustomerAvatar(code: string, store: string): Promise<void> {
  const response = await httpDelete<ApiSuccessResponse<{ deleted?: boolean }>>(
    customerAvatarUrl(code, store),
  );
  unwrapEnvelope(response, "Erro ao remover logo do cliente.");
}

export async function deactivateSellerPortfolio(sellerId: string): Promise<SellerPortfolio> {
  const response = await httpDelete<ApiSuccessResponse<SellerPortfolio>>(
    commercialApiUrl(`/seller-portfolios/${encodeURIComponent(sellerId)}`),
  );
  return unwrapEnvelope(response, "Erro ao desativar carteira.");
}

export async function updateSellerPortfolio(
  sellerId: string,
  input: { display_name?: string; active?: boolean },
): Promise<SellerPortfolio> {
  const response = await httpPatch<ApiSuccessResponse<SellerPortfolio>>(
    commercialApiUrl(`/seller-portfolios/${encodeURIComponent(sellerId)}`),
    input,
  );
  return unwrapEnvelope(response, "Erro ao atualizar carteira.");
}
