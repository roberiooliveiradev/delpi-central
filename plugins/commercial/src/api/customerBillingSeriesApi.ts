import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import {
  CUSTOMER_BATCH_CONCURRENCY,
  CUSTOMER_BATCH_SIZE,
} from "../config/customerBatching";
import { runDeterministicBatches } from "../utils/deterministicBatch";
import { apiDelpiUrl, httpPost } from "./httpClient";

export type CustomerBillingSeriesPoint = {
  month: string;
  label: string;
  value: number;
  date_start: string;
  date_end: string;
};

export type CustomerBillingSeriesPayload = {
  months: number;
  customer_count: number;
  points: CustomerBillingSeriesPoint[];
  coverage: { covered: number; total: number; failedBatches: number };
  partialError: string | null;
};

async function fetchCustomerBillingSeriesBatch(
  customers: Array<{ customer_code: string; customer_store: string }>,
  options?: { months?: number; signal?: AbortSignal },
): Promise<Omit<CustomerBillingSeriesPayload, "coverage" | "partialError">> {
  const response = await httpPost<ApiSuccessResponse<CustomerBillingSeriesPayload>>(
    apiDelpiUrl("/pedidos-venda-abertos/customers/billing-series"),
    {
      customers,
      months: options?.months ?? 12,
    },
    { signal: options?.signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar faturamento mensal.");
}

export async function fetchCustomerBillingSeries(
  customers: Array<{ customer_code: string; customer_store: string }>,
  options?: { months?: number; signal?: AbortSignal },
): Promise<CustomerBillingSeriesPayload> {
  const execution = await runDeterministicBatches(customers, {
    chunkSize: CUSTOMER_BATCH_SIZE,
    concurrency: CUSTOMER_BATCH_CONCURRENCY,
    signal: options?.signal,
    execute: (batch) => fetchCustomerBillingSeriesBatch([...batch], {
      months: options?.months,
      signal: options?.signal,
    }),
  });
  const byMonth = new Map<string, CustomerBillingSeriesPoint>();
  let covered = 0;
  for (const batch of execution.batches) {
    if (!batch.value) continue;
    const reportedCount = Number(batch.value.customer_count);
    covered += Number.isFinite(reportedCount)
      ? Math.max(0, Math.min(batch.inputCount, Math.trunc(reportedCount)))
      : batch.inputCount;
    for (const point of batch.value.points ?? []) {
      const existing = byMonth.get(point.month);
      byMonth.set(point.month, {
        ...(existing ?? point),
        value: (existing?.value ?? 0) + (Number(point.value) || 0),
      });
    }
  }
  const points = [...byMonth.values()].sort((a, b) => {
    const byDate = a.date_start.localeCompare(b.date_start);
    return byDate || a.month.localeCompare(b.month);
  });
  return {
    months: options?.months ?? 12,
    customer_count: covered,
    points,
    coverage: { covered, total: customers.length, failedBatches: execution.failedBatches },
    partialError: execution.failedBatches > 0 || covered < customers.length
      ? `Faturamento parcial: ${covered} de ${customers.length} clientes cobertos; ${execution.failedBatches} lote(s) falharam.`
      : null,
  };
}
