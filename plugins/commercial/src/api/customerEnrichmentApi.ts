/**
 * Enrichment/avatar via commercial-api (não api-delpi).
 * Mantém a API de superfície do CM para o código portado.
 */
import {
  customerAvatarUrl as commercialAvatarUrl,
  deleteCustomerAvatar as commercialDeleteAvatar,
  enrichPortfolioCustomers as commercialEnrich,
  fetchCustomerAvatarObjectUrl as commercialFetchAvatar,
  upsertCustomerAvatar as commercialUpsertAvatar,
} from "./commercialPortfolioApi";
import {
  CUSTOMER_BATCH_CONCURRENCY,
  CUSTOMER_BATCH_SIZE,
} from "../config/customerBatching";
import { runDeterministicBatches } from "../utils/deterministicBatch";

export type CustomerBillingTrend = "up" | "down" | "stable" | "insufficient";

export type CustomerEnrichmentItem = {
  customer_code: string;
  customer_store: string;
  city: string | null;
  state: string | null;
  last_purchase_date: string | null;
  billed_12m: number | null;
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
  options?: { windowDays?: number },
): Promise<CustomerEnrichmentItem[]> {
  const items = await commercialEnrich(customers, signal, options);
  return items as CustomerEnrichmentItem[];
}

export type CustomerEnrichmentBatchPayload = {
  items: CustomerEnrichmentItem[];
  coverage: { covered: number; total: number; failedBatches: number };
  partialError: string | null;
};

export async function enrichPortfolioCustomersBatched(
  customers: Array<{ customer_code: string; customer_store: string }>,
  signal?: AbortSignal,
  options?: { windowDays?: number },
): Promise<CustomerEnrichmentBatchPayload> {
  const execution = await runDeterministicBatches(customers, {
    chunkSize: CUSTOMER_BATCH_SIZE,
    concurrency: CUSTOMER_BATCH_CONCURRENCY,
    signal,
    execute: (batch) => enrichPortfolioCustomers([...batch], signal, options),
  });
  const byKey = new Map<string, CustomerEnrichmentItem>();
  for (const batch of execution.batches) {
    for (const item of batch.value ?? []) {
      const key = `${item.customer_code}|${item.customer_store}`;
      if (!byKey.has(key)) byKey.set(key, item);
    }
  }
  const items = customers
    .map((customer) => byKey.get(`${customer.customer_code}|${customer.customer_store}`))
    .filter((item): item is CustomerEnrichmentItem => Boolean(item));
  const missing = customers.length - items.length;
  return {
    items,
    coverage: { covered: items.length, total: customers.length, failedBatches: execution.failedBatches },
    partialError: execution.failedBatches > 0 || missing > 0
      ? `Cobertura parcial: ${items.length} de ${customers.length} clientes enriquecidos; ${execution.failedBatches} lote(s) falharam.`
      : null,
  };
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
