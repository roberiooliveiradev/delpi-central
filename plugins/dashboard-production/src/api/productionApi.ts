import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type { ChartGranularity } from "../types/chart";
import type {
  DepreciationPctData,
  DirectLaborCostPctData,
  OeePctData,
  OtdPctData,
  ProductionCostPctData,
  ProductionFilterParams,
  ProductionOeeSeriesData,
  ProductionOtdSeriesData,
  ProductionOtdData,
  ProductionOtdParams,
} from "../types/production";

export const PRODUCTION_API_BASE = "/apps/api-delpi/production";

function buildQuery(
  params: ProductionFilterParams | ProductionOtdParams = {}
): string {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set("start_date", params.start_date);
  if (params.end_date) searchParams.set("end_date", params.end_date);
  if (params.branch) searchParams.set("branch", params.branch);
  if (params.granularity) searchParams.set("granularity", params.granularity);

  if ("status" in params && params.status) {
    searchParams.set("status", params.status);
  }
  if ("page" in params && params.page) {
    searchParams.set("page", String(params.page));
  }
  if ("page_size" in params && params.page_size) {
    searchParams.set("page_size", String(params.page_size));
  }

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function fetchProductionData<T>(
  path: string,
  params: ProductionFilterParams | ProductionOtdParams = {},
  signal?: AbortSignal
): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${PRODUCTION_API_BASE}${path}${buildQuery(params)}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro na API de produção");
}

export function getDirectLaborCostPct(
  params: ProductionFilterParams,
  signal?: AbortSignal
) {
  return fetchProductionData<DirectLaborCostPctData>(
    "/direct_labor_cost_pct",
    params,
    signal
  );
}

export function getProductionCostPct(
  params: ProductionFilterParams,
  signal?: AbortSignal
) {
  return fetchProductionData<ProductionCostPctData>(
    "/production_cost_pct",
    params,
    signal
  );
}

export function getDepreciationPct(
  params: ProductionFilterParams,
  signal?: AbortSignal
) {
  return fetchProductionData<DepreciationPctData>(
    "/depreciation_pct",
    params,
    signal
  );
}

export function getOverallEquipmentEffectivenessPct(
  params: ProductionFilterParams,
  signal?: AbortSignal
) {
  return fetchProductionData<OeePctData>(
    "/overall_equipment_effectiveness_pct",
    params,
    signal
  );
}

export function getOnTimeDeliveryPct(
  params: ProductionFilterParams,
  signal?: AbortSignal
) {
  return fetchProductionData<OtdPctData>(
    "/on_time_delivery_pct",
    params,
    signal
  );
}

export function getProductionOeeSeries(
  params: ProductionFilterParams & { granularity: ChartGranularity },
  signal?: AbortSignal
) {
  return fetchProductionData<ProductionOeeSeriesData>(
    "/oee/series",
    params,
    signal
  );
}

export function getProductionOtdSeries(
  params: ProductionFilterParams & { granularity: ChartGranularity },
  signal?: AbortSignal
) {
  return fetchProductionData<ProductionOtdSeriesData>(
    "/otd/series",
    params,
    signal
  );
}

export function getProductionOtd(
  params: ProductionOtdParams,
  signal?: AbortSignal
) {
  return fetchProductionData<ProductionOtdData>("/otd", params, signal);
}
