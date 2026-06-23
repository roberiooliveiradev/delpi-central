import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  CpvData,
  InventoryTurnoverData,
  OtdData,
  StockValueData,
  SuppliesFilterParams,
} from "../types/supplies";

export const SUPPLIES_API_BASE = "/apps/api-delpi/supplies";

type SuppliesQueryParams = SuppliesFilterParams & {
  details_limit?: number;
  strict_idd_period?: boolean;
};

function buildQuery(params: SuppliesQueryParams = {}): string {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set("start_date", params.start_date);
  if (params.end_date) searchParams.set("end_date", params.end_date);
  if (params.branch) searchParams.set("branch", params.branch);
  if (params.location) searchParams.set("location", params.location);
  if (params.top_limit != null) {
    searchParams.set("top_limit", String(params.top_limit));
  }
  if (params.details_limit != null) {
    searchParams.set("details_limit", String(params.details_limit));
  }
  if (params.strict_idd_period != null) {
    searchParams.set("strict_idd_period", String(params.strict_idd_period));
  }
  if ((params as { summary_only?: boolean }).summary_only) {
    searchParams.set("summary_only", "true");
  }

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function fetchSuppliesData<T>(
  path: string,
  params: SuppliesFilterParams & Record<string, unknown> = {},
  signal?: AbortSignal
): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${SUPPLIES_API_BASE}${path}${buildQuery(params)}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro na API de suprimentos");
}

export function getCpv(params: SuppliesFilterParams, signal?: AbortSignal) {
  return fetchSuppliesData<CpvData>("/cpv", { ...params, top_limit: 15 }, signal);
}

export function getOtd(params: SuppliesFilterParams, signal?: AbortSignal) {
  return fetchSuppliesData<OtdData>(
    "/otd",
    { ...params, top_limit: 10, details_limit: 50 },
    signal
  );
}

export function getStockValue(
  params: Pick<
    SuppliesFilterParams,
    "branch" | "location" | "top_limit" | "start_date" | "end_date"
  > & { summary_only?: boolean },
  signal?: AbortSignal
) {
  return fetchSuppliesData<StockValueData>(
    "/stock-value",
    {
      ...params,
      top_limit: params.top_limit ?? 20,
      ...(params.summary_only ? { summary_only: true } : {}),
    },
    signal
  );
}

export function getStockValueSummary(
  params: Pick<
    SuppliesFilterParams,
    "branch" | "location" | "start_date" | "end_date"
  >,
  signal?: AbortSignal
) {
  return getStockValue({ ...params, summary_only: true }, signal);
}

export function getInventoryTurnover(
  params: SuppliesFilterParams,
  signal?: AbortSignal
) {
  return fetchSuppliesData<InventoryTurnoverData>(
    "/inventory-turnover",
    params,
    signal
  );
}
