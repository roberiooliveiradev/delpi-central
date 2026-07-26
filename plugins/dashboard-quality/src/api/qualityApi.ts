import { httpGet } from "./httpClient";
import { buildQuery } from "./query";
import {
  isNonconformitySeriesData,
  isPpmSeriesData,
  isQualityBranchesData,
  parseQualityApiEnvelope,
} from "./validateQualityResponse";
import type { ApiSuccessResponse } from "../types/api";
import type { Page } from "../types/pagination";
import type {
  Audit5sSummary,
  Audit5sSummaryParams,
} from "../types/audit5s";
import type {
  KaizenSummary,
  KaizenSummaryParams,
  KaizenDetail,
} from "../types/kaizen";
import type {
  ListNonconformitiesParams,
  Nonconformity,
  NonconformitySeriesResponse,
} from "../types/nonconformity";
import type { ChartGranularity } from "../types/chart";
import type {
  DateRangeParams,
  ListPpmParams,
  PpmItem,
  PpmSeriesResponse,
  PpmSummary,
  PpmType,
} from "../types/ppm";
import type { CostPctSummary } from "../types/losses";

export type QualityBranchesResponse = {
  branches: string[];
};

export const QUALITY_API_BASE = "/apps/api-delpi/quality";

async function fetchQualityData<T>(
  path: string,
  params: Record<string, string | number | undefined | null> = {},
  signal?: AbortSignal
): Promise<T> {
  const query = buildQuery(params);
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${QUALITY_API_BASE}${path}${query}`,
    { signal }
  );

  if (response.success === false) {
    throw new Error(response.message || "Erro na API de qualidade");
  }

  return response.data;
}

async function fetchQualityDataValidated<T>(
  path: string,
  params: Record<string, string | number | undefined | null>,
  validateData: (data: unknown) => data is T,
  signal?: AbortSignal
): Promise<T> {
  const query = buildQuery(params);
  const response = await httpGet<unknown>(
    `${QUALITY_API_BASE}${path}${query}`,
    { signal }
  );

  return parseQualityApiEnvelope(response, validateData).data;
}

export async function listNonconformities(
  params: ListNonconformitiesParams = {},
  signal?: AbortSignal
): Promise<Page<Nonconformity>> {
  return fetchQualityData<Page<Nonconformity>>(
    "/nonconformities",
    {
      type: params.type ?? "all",
      branch: params.branch,
      start_date: params.start_date,
      end_date: params.end_date,
      status: params.status,
      item_code: params.item_code,
      description: params.description,
      page: params.page,
      page_size: params.page_size,
    },
    signal
  );
}

export async function getKaizenSummary(
  params: KaizenSummaryParams = {},
  signal?: AbortSignal
): Promise<KaizenSummary> {
  return fetchQualityData<KaizenSummary>("/kaizens/summary", params, signal);
}

export async function getKaizenById(
  kaizenId: string,
  signal?: AbortSignal
): Promise<KaizenDetail> {
  const encoded = encodeURIComponent(kaizenId.trim());
  return fetchQualityData<KaizenDetail>(`/kaizens/${encoded}`, {}, signal);
}

export async function getAudit5sSummary(
  params: Audit5sSummaryParams = {},
  signal?: AbortSignal
): Promise<Audit5sSummary> {
  return fetchQualityData<Audit5sSummary>(
    "/audit-5s/summary",
    params,
    signal
  );
}

export async function getScrapCostPct(
  params: DateRangeParams = {},
  signal?: AbortSignal
): Promise<CostPctSummary> {
  return fetchQualityData<CostPctSummary>("/scrap-cost-pct", {
    branch: params.branch,
    start_date: params.start_date,
    end_date: params.end_date,
  }, signal);
}

export async function getReworkCostPct(
  params: DateRangeParams = {},
  signal?: AbortSignal
): Promise<CostPctSummary> {
  return fetchQualityData<CostPctSummary>("/rework-cost-pct", {
    branch: params.branch,
    start_date: params.start_date,
    end_date: params.end_date,
  }, signal);
}

export async function getPpmSummary(
  type: PpmType,
  params: DateRangeParams = {},
  signal?: AbortSignal
): Promise<PpmSummary> {
  return fetchQualityData<PpmSummary>(
    `/ppm/${type}/summary`,
    {
      branch: params.branch,
      start_date: params.start_date,
      end_date: params.end_date,
      product_prefix: params.product_prefix,
    },
    signal
  );
}

export async function getPpmInternalSummary(
  params: DateRangeParams = {},
  signal?: AbortSignal
): Promise<PpmSummary> {
  return getPpmSummary("internal", params, signal);
}

export async function getPpmExternalSummary(
  params: DateRangeParams = {},
  signal?: AbortSignal
): Promise<PpmSummary> {
  return getPpmSummary("external", params, signal);
}

export async function listPpm(
  type: PpmType,
  params: ListPpmParams = {},
  signal?: AbortSignal
): Promise<Page<PpmItem>> {
  return fetchQualityData<Page<PpmItem>>(`/ppm/${type}`, {
    branch: params.branch,
    start_date: params.start_date,
    end_date: params.end_date,
    page: params.page,
    page_size: params.page_size,
    product_prefix: params.product_prefix,
  }, signal);
}

export async function listPpmInternal(
  params: ListPpmParams = {},
  signal?: AbortSignal
): Promise<Page<PpmItem>> {
  return listPpm("internal", params, signal);
}

export async function listPpmExternal(
  params: ListPpmParams = {},
  signal?: AbortSignal
): Promise<Page<PpmItem>> {
  return listPpm("external", params, signal);
}

export async function listQualityBranches(
  params: DateRangeParams = {},
  signal?: AbortSignal
): Promise<QualityBranchesResponse> {
  return fetchQualityDataValidated(
    "/branches",
    params,
    isQualityBranchesData,
    signal
  );
}

export async function getNonconformitySeries(
  params: Omit<ListNonconformitiesParams, "page" | "page_size"> & {
    granularity: ChartGranularity;
  },
  signal?: AbortSignal
): Promise<NonconformitySeriesResponse> {
  return fetchQualityDataValidated(
    "/nonconformities/series",
    {
      type: params.type ?? "all",
      branch: params.branch,
      start_date: params.start_date,
      end_date: params.end_date,
      status: params.status,
      item_code: params.item_code,
      description: params.description,
      granularity: params.granularity,
    },
    isNonconformitySeriesData,
    signal
  );
}

export async function getPpmSeries(
  type: PpmType,
  params: DateRangeParams & { granularity: ChartGranularity },
  signal?: AbortSignal
): Promise<PpmSeriesResponse> {
  return fetchQualityDataValidated(
    `/ppm/${type}/series`,
    {
      branch: params.branch,
      start_date: params.start_date,
      end_date: params.end_date,
      granularity: params.granularity,
      product_prefix: params.product_prefix,
    },
    isPpmSeriesData,
    signal
  );
}
