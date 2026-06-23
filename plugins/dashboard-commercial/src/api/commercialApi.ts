import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type { ChartGranularity } from "../types/chart";
import type {
  ClosingRateData,
  CommercialFilterParams,
  CommercialProposalDetail,
  CommercialProposalHistoryEvent,
  CommercialProposalsPage,
  CommercialRolSeriesData,
  NewClientsAverageData,
  NewBusinessRolPctData,
  NewClientsRolPctData,
  RolTargetData,
  SalesOrderOtdData,
} from "../types/commercial";

export const COMMERCIAL_API_BASE = "/apps/api-delpi/commercial";

const PROPOSAL_SORT_API_KEYS: Record<string, string> = {
  proposal: "proposal_number",
  customer: "customer_code",
  status: "status_code",
};

export function resolveProposalSortApiKey(
  sortKey: string | null | undefined
): string | undefined {
  if (!sortKey) return undefined;
  return PROPOSAL_SORT_API_KEYS[sortKey] ?? sortKey;
}

function buildQuery(
  params: CommercialFilterParams & { granularity?: ChartGranularity }
): string {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set("start_date", params.start_date);
  if (params.end_date) searchParams.set("end_date", params.end_date);
  if (params.branch) searchParams.set("branch", params.branch);
  if (params.customer_segment) {
    searchParams.set("customer_segment", params.customer_segment);
  }
  if (params.granularity) searchParams.set("granularity", params.granularity);
  if (params.status) searchParams.set("status", params.status);
  if (params.page != null) searchParams.set("page", String(params.page));
  if (params.page_size != null) {
    searchParams.set("page_size", String(params.page_size));
  }
  if (params.sort_by) searchParams.set("sort_by", params.sort_by);
  if (params.sort_dir) searchParams.set("sort_dir", params.sort_dir);

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function fetchCommercialData<T>(
  path: string,
  params: CommercialFilterParams = {},
  signal?: AbortSignal
): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${COMMERCIAL_API_BASE}${path}${buildQuery(params)}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro na API comercial");
}

export function getHeadOfficeRolTarget(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<RolTargetData>(
    "/head_office_rol_target_pct",
    params,
    signal
  );
}

export function getBranchRolTarget(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<RolTargetData>(
    "/branch_rol_target_pct",
    params,
    signal
  );
}

export function getClosingRate(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<ClosingRateData>("/closing-rate", params, signal);
}

export function getCommercialProposals(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<CommercialProposalsPage>(
    "/proposals",
    params,
    signal
  );
}

export async function getCommercialProposalsForExport(
  params: CommercialFilterParams & {
    total: number;
    sort_by?: string;
    sort_dir?: "asc" | "desc";
  },
  signal?: AbortSignal
): Promise<CommercialProposalsPage> {
  const { total, ...query } = params;
  return getCommercialProposals(
    {
      ...query,
      page: 1,
      page_size: Math.min(Math.max(total, 1), 200),
    },
    signal
  );
}

export function getCommercialProposalByNumber(
  proposalNumber: string,
  params: {
    branch: string;
    revision?: string;
  },
  signal?: AbortSignal
) {
  const searchParams = new URLSearchParams();
  searchParams.set("branch", params.branch);
  if (params.revision) searchParams.set("revision", params.revision);

  const encoded = encodeURIComponent(proposalNumber.trim());
  const query = searchParams.toString();

  return httpGet<ApiSuccessResponse<CommercialProposalDetail>>(
    `${COMMERCIAL_API_BASE}/proposals/${encoded}${query ? `?${query}` : ""}`,
    { signal }
  ).then((response) =>
    unwrapApiDelpiEnvelope(response, "Erro ao carregar detalhe da proposta")
  );
}

export function getCommercialProposalHistoryEvents(
  proposalNumber: string,
  params: {
    branch: string;
    revision?: string;
    start_date?: string;
    end_date?: string;
  },
  signal?: AbortSignal
) {
  const searchParams = new URLSearchParams();
  searchParams.set("branch", params.branch);
  if (params.revision) searchParams.set("revision", params.revision);
  if (params.start_date) searchParams.set("date_start", params.start_date);
  if (params.end_date) searchParams.set("date_end", params.end_date);

  const encoded = encodeURIComponent(proposalNumber.trim());
  const query = searchParams.toString();

  return httpGet<
    ApiSuccessResponse<{
      items: CommercialProposalHistoryEvent[];
      total: number;
      reference_revision?: string | null;
    }>
  >(
    `${COMMERCIAL_API_BASE}/proposals/${encoded}/history/events${
      query ? `?${query}` : ""
    }`,
    { signal }
  ).then((response) =>
    unwrapApiDelpiEnvelope(response, "Erro ao carregar histórico da proposta")
  );
}

export function getNewClientsAverage(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<NewClientsAverageData>(
    "/new-clients-average",
    params,
    signal
  );
}

export function getSalesOrderOtd(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<SalesOrderOtdData>(
    "/sales-order-otd",
    params,
    signal
  );
}

export function getNewBusinessRolPct(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<NewBusinessRolPctData>(
    "/new-business-rol-pct",
    params,
    signal
  );
}

export function getNewClientsRolPct(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<NewClientsRolPctData>(
    "/new-clients-rol-pct",
    params,
    signal
  );
}

export function getCommercialRolSeries(
  params: Pick<
    CommercialFilterParams,
    "start_date" | "end_date" | "customer_segment"
  > & {
    granularity: ChartGranularity;
  },
  signal?: AbortSignal
) {
  return fetchCommercialData<CommercialRolSeriesData>(
    "/rol/series",
    params,
    signal
  );
}
