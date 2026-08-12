import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  ChartGranularity,
  ClosingRateData,
  CommercialProposalDetail,
  CommercialProposalHistoryEventsData,
  CommercialProposalsPage,
  CommercialRolSeriesData,
  AnalyticsFilterParams,
  NewBusinessRolPctData,
  RolTargetData,
  SalesOrderOtdData,
  SalesOrderOtdLineDetailData,
  SalesOrderOtdPanelData,
  SalesOrderOtdSeriesData,
} from "../types/analytics";
import { commercialApiUrl, httpGet } from "./httpClient";

/** BFF commercial-api — membership/seller_id no servidor; TOTVS via gateway. */
const ANALYTICS_PATH = "/analytics";

function buildQuery(
  params: AnalyticsFilterParams & { granularity?: ChartGranularity },
): string {
  const searchParams = new URLSearchParams();
  if (params.start_date) searchParams.set("start_date", params.start_date);
  if (params.end_date) searchParams.set("end_date", params.end_date);
  if (params.branch) searchParams.set("branch", params.branch);
  if (params.customer_segment) {
    searchParams.set("customer_segment", params.customer_segment);
  }
  if (params.seller_id?.trim()) {
    searchParams.set("seller_id", params.seller_id.trim());
  }
  if (params.granularity) searchParams.set("granularity", params.granularity);
  if (params.status) searchParams.set("status", params.status);
  if (params.page != null) searchParams.set("page", String(params.page));
  if (params.page_size != null) searchParams.set("page_size", String(params.page_size));
  if (params.sort_by) searchParams.set("sort_by", params.sort_by);
  if (params.sort_dir) searchParams.set("sort_dir", params.sort_dir);
  if (params.search?.trim()) searchParams.set("search", params.search.trim());
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function fetchAnalyticsData<T>(
  path: string,
  params: AnalyticsFilterParams = {},
  signal?: AbortSignal,
): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${commercialApiUrl(`${ANALYTICS_PATH}${path}`)}${buildQuery(params)}`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro na API comercial");
}

export function getHeadOfficeRolTarget(params: AnalyticsFilterParams, signal?: AbortSignal) {
  return fetchAnalyticsData<RolTargetData>("/head_office_rol_target_pct", params, signal);
}

export function getBranchRolTarget(params: AnalyticsFilterParams, signal?: AbortSignal) {
  return fetchAnalyticsData<RolTargetData>("/branch_rol_target_pct", params, signal);
}

export function getClosingRate(params: AnalyticsFilterParams, signal?: AbortSignal) {
  return fetchAnalyticsData<ClosingRateData>("/closing-rate", params, signal);
}

export function getSalesOrderOtd(params: AnalyticsFilterParams, signal?: AbortSignal) {
  return fetchAnalyticsData<SalesOrderOtdData>("/sales-order-otd", params, signal);
}

export function getNewBusinessRolPct(params: AnalyticsFilterParams, signal?: AbortSignal) {
  return fetchAnalyticsData<NewBusinessRolPctData>("/new-business-rol-pct", params, signal);
}

export function getCommercialRolSeries(
  params: Pick<AnalyticsFilterParams, "start_date" | "end_date" | "customer_segment" | "seller_id"> & {
    granularity: ChartGranularity;
  },
  signal?: AbortSignal,
) {
  return fetchAnalyticsData<CommercialRolSeriesData>("/rol/series", params, signal);
}

export function getCommercialProposals(params: AnalyticsFilterParams, signal?: AbortSignal) {
  return fetchAnalyticsData<CommercialProposalsPage>("/proposals", params, signal);
}

export function getCommercialProposalByNumber(
  proposalNumber: string,
  params: { branch: string; revision?: string; seller_id?: string },
  signal?: AbortSignal,
) {
  const searchParams = new URLSearchParams();
  searchParams.set("branch", params.branch);
  if (params.revision) searchParams.set("revision", params.revision);
  if (params.seller_id?.trim()) searchParams.set("seller_id", params.seller_id.trim());
  const encoded = encodeURIComponent(proposalNumber.trim());
  const query = searchParams.toString();
  return httpGet<ApiSuccessResponse<CommercialProposalDetail>>(
    `${commercialApiUrl(`${ANALYTICS_PATH}/proposals/${encoded}`)}${query ? `?${query}` : ""}`,
    { signal },
  ).then((response) => unwrapEnvelope(response, "Erro ao carregar detalhe da OV"));
}

export function getCommercialProposalHistoryEvents(
  proposalNumber: string,
  params: {
    branch: string;
    revision?: string;
    start_date?: string;
    end_date?: string;
    seller_id?: string;
  },
  signal?: AbortSignal,
) {
  const searchParams = new URLSearchParams();
  searchParams.set("branch", params.branch);
  if (params.revision) searchParams.set("revision", params.revision);
  if (params.start_date) searchParams.set("start_date", params.start_date);
  if (params.end_date) searchParams.set("end_date", params.end_date);
  if (params.seller_id?.trim()) searchParams.set("seller_id", params.seller_id.trim());
  const encoded = encodeURIComponent(proposalNumber.trim());
  const query = searchParams.toString();
  return httpGet<ApiSuccessResponse<CommercialProposalHistoryEventsData>>(
    `${commercialApiUrl(`${ANALYTICS_PATH}/proposals/${encoded}/history/events`)}${
      query ? `?${query}` : ""
    }`,
    { signal },
  ).then((response) =>
    unwrapEnvelope(response, "Erro ao carregar histórico da OV"),
  );
}

export function getSalesOrderOtdPanel(params: AnalyticsFilterParams, signal?: AbortSignal) {
  return fetchAnalyticsData<SalesOrderOtdPanelData>("/sales-order-otd/panel", params, signal);
}

export function getSalesOrderOtdSeries(
  params: Pick<
    AnalyticsFilterParams,
    "start_date" | "end_date" | "branch" | "customer_segment" | "seller_id"
  > & {
    granularity: ChartGranularity;
  },
  signal?: AbortSignal,
) {
  return fetchAnalyticsData<SalesOrderOtdSeriesData>("/sales-order-otd/series", params, signal);
}

export function getSalesOrderOtdLineDetail(
  branch: string,
  orderNumber: string,
  lineItem: string,
  params: Pick<AnalyticsFilterParams, "start_date" | "end_date" | "customer_segment" | "seller_id">,
  signal?: AbortSignal,
) {
  const encodedBranch = encodeURIComponent(branch);
  const encodedOrder = encodeURIComponent(orderNumber);
  const encodedLine = encodeURIComponent(lineItem);
  return httpGet<ApiSuccessResponse<SalesOrderOtdLineDetailData>>(
    `${commercialApiUrl(
      `${ANALYTICS_PATH}/sales-order-otd/lines/${encodedBranch}/${encodedOrder}/${encodedLine}`,
    )}${buildQuery(params)}`,
    { signal },
  ).then((response) =>
    unwrapEnvelope(response, "Erro ao carregar detalhe da linha de pedido"),
  );
}
