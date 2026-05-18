import { httpGet } from "./httpClient";
import { buildQuery } from "./query";
import type { ApiSuccessResponse } from "../types/api";
import type { Page } from "../types/pagination";
import type {
  Audit5sSummary,
  Audit5sSummaryParams,
} from "../types/audit5s";
import type {
  KaizenSummary,
  KaizenSummaryParams,
} from "../types/kaizen";
import type {
  ListNonconformitiesParams,
  Nonconformity,
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

export async function listNonconformities(
  params: ListNonconformitiesParams = {},
  signal?: AbortSignal
): Promise<Page<Nonconformity>> {
  return fetchQualityData<Page<Nonconformity>>(
    "/nonconformities",
    {
      type: params.type ?? "all",
      branch: params.branch,
      date_start: params.date_start,
      date_end: params.date_end,
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

export async function getPpmSummary(
  type: PpmType,
  params: DateRangeParams = {},
  signal?: AbortSignal
): Promise<PpmSummary> {
  return fetchQualityData<PpmSummary>(
    `/ppm/${type}/summary`,
    params,
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
  return fetchQualityData<Page<PpmItem>>(`/ppm/${type}`, params, signal);
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
  return fetchQualityData<QualityBranchesResponse>("/branches", params, signal);
}

export async function getPpmSeries(
  type: PpmType,
  params: DateRangeParams & { granularity: ChartGranularity },
  signal?: AbortSignal
): Promise<PpmSeriesResponse> {
  return fetchQualityData<PpmSeriesResponse>(
    `/ppm/${type}/series`,
    {
      branch: params.branch,
      date_start: params.date_start,
      date_end: params.date_end,
      granularity: params.granularity,
    },
    signal
  );
}
