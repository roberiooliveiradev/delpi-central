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

const ENGINEERING_API_BASE = "/apps/engineering-api/v1";

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

/** Datas ISO (YYYY-MM-DD) — contrato E-LMP-*; YYYYMMDD é normalizado. */
function toApiDate(value?: string): string | undefined {
  if (!value) return undefined;
  const normalized = value.trim();
  if (/^\d{8}$/.test(normalized)) {
    return `${normalized.slice(0, 4)}-${normalized.slice(4, 6)}-${normalized.slice(6, 8)}`;
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

type EngineeringData = Record<string, unknown> & { status?: string };

function assertAvailable(data: EngineeringData, fallback: string): void {
  if (data.status && data.status !== "available" && data.status !== "empty") {
    const reason =
      (typeof data.message === "string" && data.message) ||
      (typeof data.reason === "string" && data.reason) ||
      data.status;
    throw new Error(`${fallback} (${reason})`);
  }
}

async function fetchLmpData<T>(
  path: string,
  params: LmpsDashboardParams | ListLmpsParams = {},
  signal?: AbortSignal,
  fallbackMessage = "Erro na API de LMPs",
): Promise<T> {
  const query = buildQuery(params);
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${ENGINEERING_API_BASE}${path}${query}`,
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
    `${ENGINEERING_API_BASE}/lmps${query}`,
    { signal },
  );
  const data = unwrapApiDelpiEnvelope(response, "Erro ao listar LMPs");
  assertAvailable(data as EngineeringData, "Fonte de LMPs indisponível");
  return data;
}

export async function getLmpsDashboard(
  params: LmpsDashboardParams,
  signal?: AbortSignal
): Promise<LmpsDashboardResponse> {
  const data = await fetchLmpData<EngineeringData & LmpsDashboardResponse>(
    "/lmps",
    params,
    signal,
    "Erro ao carregar dashboard de LMPs",
  );
  assertAvailable(data, "Fonte de LMPs indisponível");
  return data;
}

export async function getLmpsDashboardSummary(
  params: LmpsDashboardParams,
  signal?: AbortSignal,
): Promise<LmpsDashboardSummary> {
  const data = await fetchLmpData<EngineeringData & LmpsDashboardSummary>(
    "/lmps/summary",
    params,
    signal,
    "Erro ao carregar KPIs de LMPs",
  );
  assertAvailable(data, "Fonte de KPIs de LMPs indisponível");
  return data;
}

export async function getLmpsDashboardCharts(
  params: LmpsDashboardParams,
  signal?: AbortSignal,
): Promise<LmpsDashboardCharts> {
  // E-LMP-01 carrega os agregados R11 no mesmo payload dos itens — o
  // hook reutiliza a resposta de getLmpsDashboardItems; este adapter
  // permanece por compatibilidade de assinatura e faz a leitura direta.
  const data = await fetchLmpData<EngineeringData & LmpsDashboardResponse>(
    "/lmps",
    params,
    signal,
    "Erro ao carregar gráficos de LMPs",
  );
  assertAvailable(data, "Fonte de gráficos indisponível");
  return data.charts ?? {};
}

export type LmpsDashboardItemsResponse = {
  items: LmpDashboardItem[];
  total: number;
  page: number;
  page_size: number;
  summary?: LmpsDashboardSummary;
  charts?: LmpsDashboardCharts;
};

export type GetLmpBySaleNumberParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
  revision?: string;
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
  if (params.revision) searchParams.set("revision", params.revision);

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

  const response = await httpGet<
    ApiSuccessResponse<EngineeringData & { item?: LmpDetailData }>
  >(`${ENGINEERING_API_BASE}/lmps/${encoded}${query}`, { signal });

  const data = unwrapApiDelpiEnvelope(response, "Erro ao carregar detalhe da OV");
  assertAvailable(data, "Fonte de detalhe indisponível");
  return (data.item ?? (data as LmpDetailData)) as LmpDetailData;
}

export async function getLmpHistoryEvents(
  saleNumber: string,
  params: GetLmpBySaleNumberParams = {},
  signal?: AbortSignal,
): Promise<LmpHistoryCollectionResponse> {
  const query = buildLmpDetailQuery(params);
  const encoded = encodeURIComponent(String(saleNumber).trim());

  const response = await httpGet<
    ApiSuccessResponse<EngineeringData & LmpHistoryCollectionResponse>
  >(
    `${ENGINEERING_API_BASE}/lmps/${encoded}/history/events${query}`,
    { signal },
  );

  const data = unwrapApiDelpiEnvelope(response, "Erro ao carregar histórico da OV");
  assertAvailable(data, "Fonte de histórico indisponível");
  return { ...data, sale_number: saleNumber };
}

export async function getLmpHistoryFlow(
  saleNumber: string,
  params: GetLmpBySaleNumberParams = {},
  signal?: AbortSignal,
): Promise<LmpHistoryCollectionResponse> {
  const query = buildLmpDetailQuery(params);
  const encoded = encodeURIComponent(String(saleNumber).trim());

  const response = await httpGet<
    ApiSuccessResponse<EngineeringData & LmpHistoryCollectionResponse>
  >(
    `${ENGINEERING_API_BASE}/lmps/${encoded}/history/flow${query}`,
    { signal },
  );

  const data = unwrapApiDelpiEnvelope(response, "Erro ao carregar fluxo da OV");
  assertAvailable(data, "Fonte de fluxo indisponível");
  return { ...data, sale_number: saleNumber };
}

export async function getLmpsDashboardItems(
  params: LmpsDashboardParams,
  signal?: AbortSignal,
): Promise<LmpsDashboardItemsResponse> {
  const data = await fetchLmpData<EngineeringData & LmpsDashboardItemsResponse>(
    "/lmps",
    params,
    signal,
    "Erro ao carregar itens de LMPs",
  );
  assertAvailable(data, "Fonte de itens indisponível");
  return data;
}

export type LmpGoalContextResponse = {
  status?: string;
  data?: DashboardGoalFields;
};

/** Metas do indicador LMP — owner Strategic Indicators via adapter
 * governado `GET /v1/lmps/goal-context` (delegação do Bearer humano).
 * Forbidden/unavailable retornam estado explícito — nunca meta falsa. */
export async function getLmpGoalContext(
  params: LmpsDashboardParams = {},
  signal?: AbortSignal,
): Promise<DashboardGoalFields | null> {
  const query = buildQuery(params);
  const response = await httpGet<
    ApiSuccessResponse<{ status?: string; data?: DashboardGoalFields }>
  >(`${ENGINEERING_API_BASE}/lmps/goal-context${query}`, { signal }).catch(
    () => null,
  );
  if (!response) return null;
  const data = unwrapApiDelpiEnvelope(response, "Erro ao carregar metas");
  if (data.status !== "available" || !data.data) return null;
  return data.data;
}
