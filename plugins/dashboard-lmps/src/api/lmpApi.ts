import { httpGet } from "./httpClient";
import type {
  ApiSuccessResponse,
  ListLmpsParams,
  LmpItem,
  LmpDashboardItem,
  Page,
} from "../types/lmp";

export type LmpsDashboardSummary = {
  total_lmps: number;
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

  const dateStart = toApiDate(params.date_start);
  const dateEnd = toApiDate(params.date_end);

  if (dateStart) searchParams.set("date_start", dateStart);
  if (dateEnd) searchParams.set("date_end", dateEnd);
  if (params.branch) searchParams.set("branch", params.branch);
  if (params.listing_type && params.listing_type !== "Todos") {
    searchParams.set("listing_type", params.listing_type);
  }
  if (params.status) searchParams.set("status", params.status);
  if (params.page) searchParams.set("page", String(params.page));
  if (params.page_size) searchParams.set("page_size", String(params.page_size));

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function listLmps(
  params: ListLmpsParams,
  signal?: AbortSignal
): Promise<Page<LmpItem>> {
  const query = buildQuery(params);

  const response = await httpGet<ApiSuccessResponse<Page<LmpItem>>>(
    `/apps/api-delpi/engineering/lmps/${query}`,
    { signal }
  );

  return response.data;
}

export async function getLmpsDashboard(
  params: LmpsDashboardParams,
  signal?: AbortSignal
): Promise<LmpsDashboardResponse> {
  const query = buildQuery(params);

  const response = await httpGet<ApiSuccessResponse<LmpsDashboardResponse>>(
    `/apps/api-delpi/engineering/lmps/dashboard${query}`,
    { signal }
  );

  return response.data;
}