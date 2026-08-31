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
  OpenPortfolioHorizonData,
  OpenPortfolioSummaryData,
  PortfolioBillingRankingData,
  PortfolioBillingShareData,
  RolTargetData,
  SalesConversionRateSeriesData,
  SalesOrderOtdData,
  SalesOrderOtdLineDetailData,
  SalesOrderOtdPanelData,
  SalesOrderOtdSeriesData,
} from "../types/analytics";
import { commercialApiUrl, httpGet } from "./httpClient";

/** BFF commercial-api — membership/seller_id no servidor; TOTVS via gateway. */
const ANALYTICS_PATH = "/analytics";

function buildQuery(
  params: AnalyticsFilterParams & {
    granularity?: ChartGranularity;
    group_by?: string;
    limit?: number;
    order?: "growth" | "decline";
  },
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
  if (params.account_customer_code?.trim()) {
    searchParams.set("account_customer_code", params.account_customer_code.trim());
  }
  if (params.granularity) searchParams.set("granularity", params.granularity);
  if (params.status) searchParams.set("status", params.status);
  if (params.page != null) searchParams.set("page", String(params.page));
  if (params.page_size != null) searchParams.set("page_size", String(params.page_size));
  if (params.sort_by) searchParams.set("sort_by", params.sort_by);
  if (params.sort_dir) searchParams.set("sort_dir", params.sort_dir);
  if (params.search?.trim()) searchParams.set("search", params.search.trim());
  if (params.group_by) searchParams.set("group_by", params.group_by);
  if (params.limit != null) searchParams.set("limit", String(params.limit));
  if (params.order) searchParams.set("order", params.order);
  if (params.nature === "gross" || params.nature === "net") {
    searchParams.set("nature", params.nature);
  }
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

export function getHeadOfficeWegRolTarget(params: AnalyticsFilterParams, signal?: AbortSignal) {
  return fetchAnalyticsData<RolTargetData>("/head_office_weg_rol_target_pct", params, signal);
}

export function getBranchWegRolTarget(params: AnalyticsFilterParams, signal?: AbortSignal) {
  return fetchAnalyticsData<RolTargetData>("/branch_weg_rol_target_pct", params, signal);
}

export function getHeadOfficeNewBusinessRolTarget(
  params: AnalyticsFilterParams,
  signal?: AbortSignal,
) {
  return fetchAnalyticsData<RolTargetData>(
    "/head_office_new_business_rol_target_pct",
    params,
    signal,
  );
}

export function getBranchNewBusinessRolTarget(
  params: AnalyticsFilterParams,
  signal?: AbortSignal,
) {
  return fetchAnalyticsData<RolTargetData>(
    "/branch_new_business_rol_target_pct",
    params,
    signal,
  );
}

export function getClosingRate(params: AnalyticsFilterParams, signal?: AbortSignal) {
  return fetchAnalyticsData<ClosingRateData>("/closing-rate", params, signal);
}

/** Snapshot de carteira em aberto — ignora período; usa seller_id/escopo. */
export function getOpenPortfolioSummary(
  params: Pick<AnalyticsFilterParams, "seller_id"> = {},
  signal?: AbortSignal,
) {
  return fetchAnalyticsData<OpenPortfolioSummaryData>(
    "/open-portfolio-summary",
    { seller_id: params.seller_id },
    signal,
  );
}

/** Share ROL carteira ÷ empresa no período (KPI-PORTFOLIO-SHARE). */
export function getPortfolioBillingShare(
  params: AnalyticsFilterParams,
  signal?: AbortSignal,
) {
  return fetchAnalyticsData<PortfolioBillingShareData>(
    "/portfolio-billing-share",
    params,
    signal,
  );
}

export type OpportunityCollaboratorSummaryRow = {
  sellerCode: string;
  sellerName: string;
  openCount: number;
  wonCount: number;
  lostCount: number;
  totalCount: number;
  ageDaysAvg: number | null;
};

export function getOpportunityCollaboratorSummary(
  params: AnalyticsFilterParams,
  signal?: AbortSignal,
) {
  return fetchAnalyticsData<{
    items: OpportunityCollaboratorSummaryRow[];
    sourceCount: number;
    total: number;
    truncated: boolean;
  }>("/opportunity-collaborator-summary", params, signal);
}

/** Ranking delta % faturamento vs período −1 ano. */
export function getPortfolioBillingRanking(
  params: AnalyticsFilterParams & {
    group_by?: "customer" | "seller";
    limit?: number;
    order?: "growth" | "decline";
  },
  signal?: AbortSignal,
) {
  return fetchAnalyticsData<PortfolioBillingRankingData>(
    "/portfolio-billing-ranking",
    params,
    signal,
  );
}

/** Buckets por data_entrega — snapshot; seller_id/escopo. */
export function getOpenPortfolioHorizon(
  params: Pick<AnalyticsFilterParams, "seller_id"> = {},
  signal?: AbortSignal,
) {
  return fetchAnalyticsData<OpenPortfolioHorizonData>(
    "/open-portfolio-horizon",
    { seller_id: params.seller_id },
    signal,
  );
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

export function getSalesConversionRateSeries(
  params: Pick<AnalyticsFilterParams, "start_date" | "end_date" | "customer_segment" | "seller_id"> & {
    granularity: ChartGranularity;
  },
  signal?: AbortSignal,
) {
  return fetchAnalyticsData<SalesConversionRateSeriesData>(
    "/closing-rate/series",
    params,
    signal,
  );
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

export type DepartmentIddItem = {
  department_id: string;
  department_name?: string | null;
  score?: number | null;
  classification?: string | null;
  contribution?: number | null;
};

type DepartmentIddResponse = {
  item: DepartmentIddItem | null;
};

export async function fetchDepartmentIdd(params: {
  departmentId?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  branch?: string;
  signal?: AbortSignal;
}): Promise<DepartmentIddItem | null> {
  const searchParams = new URLSearchParams();
  searchParams.set("department_id", params.departmentId ?? "commercial");
  if (params.competence) searchParams.set("competence", params.competence);
  if (params.startDate) searchParams.set("start_date", params.startDate);
  if (params.endDate) searchParams.set("end_date", params.endDate);
  if (params.branch) searchParams.set("branch", params.branch);
  const query = searchParams.toString();
  const response = await httpGet<ApiSuccessResponse<DepartmentIddResponse>>(
    `${commercialApiUrl(`${ANALYTICS_PATH}/department-idd`)}?${query}`,
    { signal: params.signal },
  );
  const data = unwrapEnvelope(response, "Erro ao consultar IDD departamental");
  return data.item ?? null;
}

export type DepartmentIndicatorScoreItem = {
  indicator_id?: string | null;
  score?: number | null;
  name?: string | null;
};

export type DepartmentIndicatorsItem = {
  department_id: string;
  department_name?: string | null;
  score?: number | null;
  idd?: number | null;
  classification?: string | null;
  indicators?: DepartmentIndicatorScoreItem[] | null;
  partial_success?: boolean;
};

type DepartmentIndicatorsResponse = {
  item: DepartmentIndicatorsItem | null;
};

export async function fetchDepartmentIndicators(params: {
  departmentId?: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  branch?: string;
  signal?: AbortSignal;
}): Promise<DepartmentIndicatorsItem | null> {
  const searchParams = new URLSearchParams();
  searchParams.set("department_id", params.departmentId ?? "commercial");
  if (params.competence) searchParams.set("competence", params.competence);
  if (params.startDate) searchParams.set("start_date", params.startDate);
  if (params.endDate) searchParams.set("end_date", params.endDate);
  if (params.branch) searchParams.set("branch", params.branch);
  const query = searchParams.toString();
  const response = await httpGet<ApiSuccessResponse<DepartmentIndicatorsResponse>>(
    `${commercialApiUrl(`${ANALYTICS_PATH}/department-indicators`)}?${query}`,
    { signal: params.signal },
  );
  const data = unwrapEnvelope(
    response,
    "Erro ao consultar indicadores departamentais",
  );
  return data.item ?? null;
}
