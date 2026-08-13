import { commercialApiUrl, httpGet } from "./httpClient";
import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import type { SellerPortfolioAuditPage } from "../types/portfolio";

export async function listCustomerAccountAudit(
  customerCode: string,
  customerStore: string,
  options?: { page?: number; pageSize?: number; signal?: AbortSignal },
): Promise<SellerPortfolioAuditPage> {
  const params = new URLSearchParams({
    page: String(options?.page ?? 1),
    page_size: String(options?.pageSize ?? 50),
  });
  const response = await httpGet<ApiSuccessResponse<SellerPortfolioAuditPage>>(
    `${commercialApiUrl(
      `/customers/${encodeURIComponent(customerCode)}/${encodeURIComponent(customerStore)}/audit`,
    )}?${params.toString()}`,
    { signal: options?.signal },
  );
  const data = unwrapEnvelope(response, "Erro ao carregar histórico da conta.");
  return {
    items: data.items ?? [],
    total: data.total ?? 0,
    page: data.page ?? options?.page ?? 1,
    page_size: data.page_size ?? options?.pageSize ?? 50,
  };
}
