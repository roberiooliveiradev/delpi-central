import type { DashboardGoalFields } from "../utils/goalDisplay";
import { httpGet } from "./httpClient";
import {
  unwrapApiDelpiEnvelope,
  type ApiSuccessResponse,
  type ListLmpsParams,
  type LmpHistoryEvent,
  type LmpItem,
  type LmpDashboardItem,
  type LmpDetailData,
  type Page,
} from "../types/lmp";

export type LmpsDashboardSummary = DashboardGoalFields & {
  total_lmps: number;
  total_items?: number;
  percent_dentro_prazo: number;
  avg_lead_time: number;
};

export type ChartDatum = {
  name: string;
  value: number;
};

export type LeadByLevelDatum = {
  nivel: string;
  valor: number;
};

export type EvolutionDatum = {
  periodo: string;
  mediaLead: number;
  propostas: number;
};

export type LmpsDashboardCharts = {
  levelData?: ChartDatum[];
  statusData?: ChartDatum[];
  leadByLevel?: LeadByLevelDatum[];
  evolutionData?: EvolutionDatum[];
};

export type LmpsDashboardResponse = {
  items: LmpDashboardItem[];
  total: number;
  page: number;
  page_size: number;
  summary: LmpsDashboardSummary;
  charts?: LmpsDashboardCharts;
};

type LmpsDashboardParams = ListLmpsParams & {
  status?: string;
};

function toApiDate(value?: string): string | undefined {
  if (!value) return undefined;
  const normalized = value.trim();
  if (/^\d{8}$/.test(normalized)) return normalized;
  if (/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
    return normalized.replaceAll("-", "");
  }
  return normalized;
}

function buildQuery(params: ListLmpsParams & { status?: string }): string {
  const searchParams = new URLSearchParams();

  const dateStart = toApiDate(params.start_date);
  const dateEnd = toApiDate(params.end_date);

  if (dateStart) searchParams.set("start_date", dateStart);
  if (dateEnd) searchParams.set("end_date", dateEnd);
  if (params.branch) searchParams.set("branch", params.branch);
  if (params.listing_type && params.listing_type !== "Todos") {
    searchParams.set("listing_type", params.listing_type);
  }
  if (params.status && params.status !== "Todos") {
    searchParams.set("status", params.status);
  }
  if (params.page) searchParams.set("page", String(params.page));
  if (params.page_size) searchParams.set("page_size", String(params.page_size));

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function fetchLmpData<T>(
  path: string,
  params: LmpsDashboardParams | ListLmpsParams = {},
  signal?: AbortSignal,
  fallbackMessage = "Erro na API de LMPs",
): Promise<T> {
  const query = buildQuery(params);
  const response = await httpGet<ApiSuccessResponse<T>>(
    `/apps/api-delpi/engineering${path}${query}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, fallbackMessage);
}

export async function listLmps(
  params: ListLmpsParams,
  signal?: AbortSignal
): Promise<Page<LmpItem>> {
  const query = buildQuery(params);
  const response = await httpGet<ApiSuccessResponse<Page<LmpItem>>>(
    `/apps/api-delpi/engineering/lmps/${query}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao listar LMPs");
}

export async function getLmpsDashboard(
  params: LmpsDashboardParams,
  signal?: AbortSignal
): Promise<LmpsDashboardResponse> {
  return fetchLmpData<LmpsDashboardResponse>(
    "/lmps/dashboard",
    params,
    signal,
    "Erro ao carregar dashboard de LMPs",
  );
}

export async function getLmpsDashboardSummary(
  params: LmpsDashboardParams,
  signal?: AbortSignal,
): Promise<LmpsDashboardSummary> {
  return fetchLmpData<LmpsDashboardSummary>(
    "/lmps/dashboard/summary",
    params,
    signal,
    "Erro ao carregar KPIs de LMPs",
  );
}

export async function getLmpsDashboardCharts(
  params: LmpsDashboardParams,
  signal?: AbortSignal,
): Promise<LmpsDashboardCharts> {
  return fetchLmpData<LmpsDashboardCharts>(
    "/lmps/dashboard/charts",
    params,
    signal,
    "Erro ao carregar gráficos de LMPs",
  );
}

export type LmpsDashboardItemsResponse = {
  items: LmpDashboardItem[];
  total: number;
  page: number;
  page_size: number;
};

export type GetLmpBySaleNumberParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
};

export type LmpHistoryCollectionResponse = {
  sale_number: string;
  branch?: string | null;
  reference_revision?: string | null;
  panel_start_date?: string | null;
  items: LmpHistoryEvent[];
  total: number;
};

function buildLmpDetailQuery(params: GetLmpBySaleNumberParams = {}): string {
  const searchParams = new URLSearchParams();
  const dateStart = toApiDate(params.start_date);
  const dateEnd = toApiDate(params.end_date);

  if (dateStart) searchParams.set("start_date", dateStart);
  if (dateEnd) searchParams.set("end_date", dateEnd);
  if (params.branch) searchParams.set("branch", params.branch);

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function getLmpBySaleNumber(
  saleNumber: string,
  params: GetLmpBySaleNumberParams = {},
  signal?: AbortSignal
): Promise<LmpDetailData> {
  const query = buildLmpDetailQuery(params);
  const encoded = encodeURIComponent(String(saleNumber).trim());

  const response = await httpGet<ApiSuccessResponse<LmpDetailData>>(
    `/apps/api-delpi/engineering/lmps/${encoded}${query}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar detalhe da OV");
}

export async function getLmpHistoryEvents(
  saleNumber: string,
  params: GetLmpBySaleNumberParams = {},
  signal?: AbortSignal,
): Promise<LmpHistoryCollectionResponse> {
  const query = buildLmpDetailQuery(params);
  const encoded = encodeURIComponent(String(saleNumber).trim());

  const response = await httpGet<ApiSuccessResponse<LmpHistoryCollectionResponse>>(
    `/apps/api-delpi/engineering/lmps/${encoded}/history/events${query}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar histórico da OV");
}

export async function getLmpHistoryFlow(
  saleNumber: string,
  params: GetLmpBySaleNumberParams = {},
  signal?: AbortSignal,
): Promise<LmpHistoryCollectionResponse> {
  const query = buildLmpDetailQuery(params);
  const encoded = encodeURIComponent(String(saleNumber).trim());

  const response = await httpGet<ApiSuccessResponse<LmpHistoryCollectionResponse>>(
    `/apps/api-delpi/engineering/lmps/${encoded}/history/flow${query}`,
    { signal },
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar fluxo da OV");
}

export async function getLmpsDashboardItems(
  params: LmpsDashboardParams,
  signal?: AbortSignal,
): Promise<LmpsDashboardItemsResponse> {
  return fetchLmpData<LmpsDashboardItemsResponse>(
    "/lmps/dashboard/items",
    params,
    signal,
    "Erro ao carregar itens de LMPs",
  );
}