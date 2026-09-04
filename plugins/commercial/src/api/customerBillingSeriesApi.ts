import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import {
  CUSTOMER_BATCH_CONCURRENCY,
  CUSTOMER_BATCH_SIZE,
} from "../config/customerBatching";
import { runDeterministicBatches } from "../utils/deterministicBatch";
import { commercialApiUrl, httpPost } from "./httpClient";

export type CustomerBillingSeriesPoint = {
  month: string;
  label: string;
  value: number;
  date_start: string;
  date_end: string;
};

export type CustomerBillingSeriesQuery = {
  months?: number;
  startDate?: string;
  endDate?: string;
  granularity?: "day" | "week" | "month" | "year";
  nature?: "gross" | "net";
  metric?: "value" | "quantity";
  productCodes?: string[];
  productGroups?: string[];
  market?: "domestic" | "export";
  signal?: AbortSignal;
};

export type CustomerBillingSeriesPayload = {
  months: number;
  customer_count: number;
  granularity?: string;
  start_date?: string;
  end_date?: string;
  metric?: "value" | "quantity";
  unit?: string | null;
  mixed_units?: boolean;
  points: CustomerBillingSeriesPoint[];
  coverage: { covered: number; total: number; failedBatches: number };
  partialError: string | null;
};

function billingSeriesBody(options?: CustomerBillingSeriesQuery) {
  return {
    months: options?.months ?? 12,
    ...(options?.startDate && options?.endDate
      ? { start_date: options.startDate, end_date: options.endDate }
      : {}),
    ...(options?.granularity ? { granularity: options.granularity } : {}),
    ...(options?.nature ? { nature: options.nature } : {}),
    ...(options?.metric ? { metric: options.metric } : {}),
    ...(options?.productCodes?.length
      ? { product_codes: options.productCodes }
      : {}),
    ...(options?.productGroups?.length
      ? { product_groups: options.productGroups }
      : {}),
    ...(options?.market ? { market: options.market } : {}),
  };
}

async function fetchCustomerBillingSeriesBatch(
  customers: Array<{ customer_code: string; customer_store: string }>,
  options?: CustomerBillingSeriesQuery,
): Promise<Omit<CustomerBillingSeriesPayload, "coverage" | "partialError">> {
  const response = await httpPost<ApiSuccessResponse<CustomerBillingSeriesPayload>>(
    commercialApiUrl("/customers/billing-series"),
    {
      customers,
      ...billingSeriesBody(options),
    },
    { signal: options?.signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar faturamento mensal.");
}

export async function fetchCustomerBillingSeries(
  customers: Array<{ customer_code: string; customer_store: string }>,
  options?: CustomerBillingSeriesQuery,
): Promise<CustomerBillingSeriesPayload> {
  const execution = await runDeterministicBatches(customers, {
    chunkSize: CUSTOMER_BATCH_SIZE,
    concurrency: CUSTOMER_BATCH_CONCURRENCY,
    signal: options?.signal,
    execute: (batch) => fetchCustomerBillingSeriesBatch([...batch], {
      months: options?.months,
      startDate: options?.startDate,
      endDate: options?.endDate,
      granularity: options?.granularity,
      nature: options?.nature,
      metric: options?.metric,
      productCodes: options?.productCodes,
      productGroups: options?.productGroups,
      market: options?.market,
      signal: options?.signal,
    }),
  });
  const byMonth = new Map<string, CustomerBillingSeriesPoint>();
  let covered = 0;
  let mixedUnits = false;
  const units = new Set<string>();
  for (const batch of execution.batches) {
    if (!batch.value) continue;
    if (batch.value.mixed_units) mixedUnits = true;
    const unit = (batch.value.unit || "").trim();
    if (unit) units.add(unit);
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
  if (mixedUnits || units.size > 1) {
    mixedUnits = true;
  }
  return {
    months: options?.months ?? 12,
    customer_count: covered,
    metric: options?.metric ?? "value",
    unit: mixedUnits || units.size !== 1 ? null : [...units][0] ?? null,
    mixed_units: mixedUnits,
    points,
    coverage: { covered, total: customers.length, failedBatches: execution.failedBatches },
    partialError: execution.failedBatches > 0 || covered < customers.length
      ? `Faturamento parcial: ${covered} de ${customers.length} clientes cobertos; ${execution.failedBatches} lote(s) falharam.`
      : null,
  };
}
