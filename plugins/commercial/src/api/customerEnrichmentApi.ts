/**
 * Enrichment/avatar via commercial-api (não api-delpi).
 * Mantém a API de superfície do PVA para o código portado.
 */
import {
  customerAvatarUrl as commercialAvatarUrl,
  deleteCustomerAvatar as commercialDeleteAvatar,
  enrichPortfolioCustomers as commercialEnrich,
  fetchCustomerAvatarObjectUrl as commercialFetchAvatar,
  upsertCustomerAvatar as commercialUpsertAvatar,
} from "./commercialPortfolioApi";

export type CustomerBillingTrend = "up" | "down" | "stable" | "insufficient";

export type CustomerEnrichmentItem = {
  customer_code: string;
  customer_store: string;
  city: string | null;
  state: string | null;
  last_purchase_date: string | null;
  billed_12m: number;
  billed_recent_6m?: number;
  billed_prior_6m?: number;
  billing_trend?: CustomerBillingTrend;
  billing_trend_pct?: number | null;
  has_avatar: boolean;
  avatar_url: string | null;
};

export function customerAvatarUrl(code: string, store: string): string {
  return commercialAvatarUrl(code, store);
}

export async function enrichPortfolioCustomers(
  customers: Array<{ customer_code: string; customer_store: string }>,
  signal?: AbortSignal,
): Promise<CustomerEnrichmentItem[]> {
  const items = await commercialEnrich(customers, signal);
  return items as CustomerEnrichmentItem[];
}

export async function upsertCustomerAvatar(
  code: string,
  store: string,
  file: File,
): Promise<{ has_avatar: boolean }> {
  await commercialUpsertAvatar(code, store, file);
  return { has_avatar: true };
}

export async function deleteCustomerAvatar(code: string, store: string): Promise<void> {
  await commercialDeleteAvatar(code, store);
}

export async function fetchCustomerAvatarObjectUrl(
  code: string,
  store: string,
  signal?: AbortSignal,
): Promise<string | null> {
  return commercialFetchAvatar(code, store, signal);
}
