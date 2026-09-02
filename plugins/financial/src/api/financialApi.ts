import { financialApiUrl, httpGet, unwrapEnvelope } from "./httpClient";
import { buildQuery } from "../utils/queryParams";
import type {
  CostCenterEntriesPayload,
  CostCenterFiltersPayload,
  CostCenterRankingItem,
  CostCenterSeriesPoint,
  CostCenterSummary,
  DelinquencyAgingBucket,
  DelinquencyCustomer,
  DelinquencyCustomersPayload,
  DelinquencyMonthPoint,
  DelinquencySummary,
  DelinquencyTitlesPayload,
  DepartmentIndicators,
  FinancialBranch,
  FreightDashboardPayload,
  FreightInconsistenciesPayload,
  GlobalIndicators,
  BillingDashboard,
  BillingInvoicesPayload,
  OverviewPayload,
  Period,
  SubpluginsPayload,
} from "../types";

type Envelope<T> = { success: boolean; message?: string; data: T };

/** O consolidado vai como `all`; o BFF exige as duas permissões de filial. */
function branchParam(branch: FinancialBranch): string {
  return branch;
}

async function get<T>(path: string, fallback: string, signal?: AbortSignal): Promise<T> {
  const envelope = await httpGet<Envelope<T>>(financialApiUrl(path), { signal });
  return unwrapEnvelope(envelope, fallback);
}

export function fetchSubplugins(signal?: AbortSignal): Promise<SubpluginsPayload> {
  return get<SubpluginsPayload>(
    "/subplugins",
    "Não foi possível carregar os subplugins.",
    signal,
  );
}

export function fetchOverview(params: {
  branch: FinancialBranch;
  startDate?: string | null;
  endDate?: string | null;
  refresh?: boolean;
  signal?: AbortSignal;
}): Promise<OverviewPayload> {
  const query = buildQuery({
    branch: branchParam(params.branch),
    startDate: params.startDate,
    endDate: params.endDate,
    refresh: params.refresh ? "true" : null,
  });
  return get<OverviewPayload>(
    `/overview${query}`,
    "Não foi possível carregar a gestão à vista.",
    params.signal,
  );
}

export function fetchBillingDashboard(params: {
  branch: FinancialBranch;
  startDate?: string | null;
  endDate?: string | null;
  granularity?: string | null;
  refresh?: boolean;
  signal?: AbortSignal;
}): Promise<BillingDashboard> {
  const query = buildQuery({
    branch: branchParam(params.branch),
    startDate: params.startDate,
    endDate: params.endDate,
    granularity: params.granularity,
    refresh: params.refresh ? "true" : null,
  });
  return get<BillingDashboard>(
    `/billing/dashboard${query}`,
    "Não foi possível carregar o faturamento.",
    params.signal,
  );
}

export function fetchBillingInvoices(params: {
  branch: FinancialBranch;
  startDate?: string | null;
  endDate?: string | null;
  signal?: AbortSignal;
}): Promise<BillingInvoicesPayload> {
  const query = buildQuery({
    branch: branchParam(params.branch),
    startDate: params.startDate,
    endDate: params.endDate,
  });
  return get<BillingInvoicesPayload>(
    `/billing/invoices${query}`,
    "Não foi possível gerar o extrato de títulos.",
    params.signal,
  );
}

// ---------------------------------------------------------------- inadimplência

type PeriodParams = {
  startDate?: string | null;
  endDate?: string | null;
  customerCode?: string | null;
  store?: string | null;
  refresh?: boolean;
  signal?: AbortSignal;
};

export function fetchDelinquencyDashboard(params: {
  startDate?: string | null;
  endDate?: string | null;
  customerCode?: string | null;
  store?: string | null;
  page?: number;
  pageSize?: number;
  sortBy?: string | null;
  sortDir?: string | null;
  onlyWithDelays?: boolean;
  refresh?: boolean;
  signal?: AbortSignal;
}): Promise<{
  summary: DelinquencySummary;
  monthly: { period: Period; items: DelinquencyMonthPoint[] };
  aging: { period: Period; items: DelinquencyAgingBucket[] };
  customers: DelinquencyCustomersPayload;
  topDelinquentCustomers: { period: Period; items: DelinquencyCustomer[] };
}> {
  const query = buildQuery({
    startDate: params.startDate,
    endDate: params.endDate,
    customerCode: params.customerCode,
    store: params.store,
    page: params.page,
    pageSize: params.pageSize,
    sortBy: params.sortBy,
    sortDir: params.sortDir,
    onlyWithDelays: params.onlyWithDelays === undefined ? null : String(params.onlyWithDelays),
    refresh: params.refresh ? "true" : null,
  });
  return get(
    `/delinquency/dashboard${query}`,
    "Não foi possível carregar a inadimplência.",
    params.signal,
  );
}

export function fetchDelinquencySummary(params: PeriodParams): Promise<DelinquencySummary> {
  const query = buildQuery({
    startDate: params.startDate,
    endDate: params.endDate,
    customerCode: params.customerCode,
    store: params.store,
    refresh: params.refresh ? "true" : null,
  });
  return get<DelinquencySummary>(
    `/delinquency/summary${query}`,
    "Não foi possível carregar a inadimplência.",
    params.signal,
  );
}

export function fetchDelinquencyMonthly(
  params: PeriodParams,
): Promise<{ period: Period; items: DelinquencyMonthPoint[] }> {
  const query = buildQuery({
    startDate: params.startDate,
    endDate: params.endDate,
    customerCode: params.customerCode,
    store: params.store,
    refresh: params.refresh ? "true" : null,
  });
  return get(
    `/delinquency/monthly${query}`,
    "Não foi possível carregar a série de inadimplência.",
    params.signal,
  );
}

export function fetchDelinquencyAging(
  params: PeriodParams,
): Promise<{ period: Period; items: DelinquencyAgingBucket[] }> {
  const query = buildQuery({
    startDate: params.startDate,
    endDate: params.endDate,
    customerCode: params.customerCode,
    store: params.store,
    refresh: params.refresh ? "true" : null,
  });
  return get(
    `/delinquency/aging${query}`,
    "Não foi possível carregar as faixas de atraso.",
    params.signal,
  );
}

export function fetchDelinquencyCustomers(params: {
  startDate?: string | null;
  endDate?: string | null;
  page?: number;
  pageSize?: number;
  sortBy?: string | null;
  sortDir?: string | null;
  search?: string | null;
  onlyWithDelays?: boolean;
  refresh?: boolean;
  signal?: AbortSignal;
}): Promise<DelinquencyCustomersPayload> {
  const query = buildQuery({
    startDate: params.startDate,
    endDate: params.endDate,
    page: params.page,
    pageSize: params.pageSize,
    sortBy: params.sortBy,
    sortDir: params.sortDir,
    search: params.search,
    onlyWithDelays: params.onlyWithDelays === undefined ? null : String(params.onlyWithDelays),
    refresh: params.refresh ? "true" : null,
  });
  return get<DelinquencyCustomersPayload>(
    `/delinquency/customers${query}`,
    "Não foi possível carregar o ranking de clientes.",
    params.signal,
  );
}

export function fetchDelinquencyTitles(params: {
  startDate?: string | null;
  endDate?: string | null;
  customerCode?: string | null;
  store?: string | null;
  status?: string | null;
  delayRange?: string | null;
  search?: string | null;
  page?: number;
  pageSize?: number;
  sortBy?: string | null;
  sortDir?: string | null;
  signal?: AbortSignal;
}): Promise<DelinquencyTitlesPayload> {
  const query = buildQuery({
    startDate: params.startDate,
    endDate: params.endDate,
    customerCode: params.customerCode,
    store: params.store,
    status: params.status,
    delayRange: params.delayRange,
    search: params.search,
    page: params.page,
    pageSize: params.pageSize,
    sortBy: params.sortBy,
    sortDir: params.sortDir,
  });
  return get<DelinquencyTitlesPayload>(
    `/delinquency/titles${query}`,
    "Não foi possível carregar os títulos do cliente.",
    params.signal,
  );
}

// ------------------------------------------------------------- centro de custo

type CostCenterParams = {
  branch: FinancialBranch;
  startDate?: string | null;
  endDate?: string | null;
  costCenter?: string | null;
  supplierCode?: string | null;
  supplierStore?: string | null;
  excludeMpProducts?: boolean;
  refresh?: boolean;
  signal?: AbortSignal;
};

function costCenterQuery(params: CostCenterParams, extra: Record<string, unknown> = {}): string {
  return buildQuery({
    branch: branchParam(params.branch),
    startDate: params.startDate,
    endDate: params.endDate,
    costCenter: params.costCenter,
    supplierCode: params.supplierCode,
    supplierStore: params.supplierStore,
    excludeMpProducts: params.excludeMpProducts ? true : null,
    refresh: params.refresh ? "true" : null,
    ...(extra as Record<string, string | number | boolean | null | undefined>),
  });
}

export function fetchCostCenterFilters(
  params: CostCenterParams,
): Promise<CostCenterFiltersPayload> {
  return get<CostCenterFiltersPayload>(
    `/cost-centers/filters${costCenterQuery({ ...params, supplierCode: null, supplierStore: null })}`,
    "Não foi possível carregar os filtros de centro de custo.",
    params.signal,
  );
}

export function fetchCostCenterSummary(params: CostCenterParams): Promise<CostCenterSummary> {
  return get<CostCenterSummary>(
    `/cost-centers/summary${costCenterQuery(params)}`,
    "Não foi possível carregar as despesas por centro de custo.",
    params.signal,
  );
}

export function fetchCostCenterSeries(
  params: CostCenterParams,
): Promise<{ period: Period; branch: string | null; items: CostCenterSeriesPoint[] }> {
  return get(
    `/cost-centers/series${costCenterQuery(params)}`,
    "Não foi possível carregar a série de despesas.",
    params.signal,
  );
}

export function fetchCostCenterRankingCenters(
  params: CostCenterParams & { limit?: number },
): Promise<{ period: Period; branch: string | null; limit: number; items: CostCenterRankingItem[] }> {
  const query = costCenterQuery({ ...params, costCenter: null }, { limit: params.limit });
  return get(
    `/cost-centers/ranking-cost-centers${query}`,
    "Não foi possível carregar o ranking de centros de custo.",
    params.signal,
  );
}

export function fetchCostCenterRankingSuppliers(
  params: CostCenterParams & { limit?: number },
): Promise<{ period: Period; branch: string | null; limit: number; items: CostCenterRankingItem[] }> {
  const query = costCenterQuery(
    { ...params, supplierCode: null, supplierStore: null },
    { limit: params.limit },
  );
  return get(
    `/cost-centers/ranking-suppliers${query}`,
    "Não foi possível carregar o ranking de fornecedores.",
    params.signal,
  );
}

export function fetchCostCenterEntries(
  params: CostCenterParams & {
    search?: string | null;
    page?: number;
    pageSize?: number;
    sortBy?: string | null;
    sortDir?: string | null;
  },
): Promise<CostCenterEntriesPayload> {
  const query = costCenterQuery(params, {
    search: params.search,
    page: params.page,
    pageSize: params.pageSize,
    sortBy: params.sortBy,
    sortDir: params.sortDir,
  });
  return get<CostCenterEntriesPayload>(
    `/cost-centers/entries${query}`,
    "Não foi possível carregar os lançamentos.",
    params.signal,
  );
}

// -------------------------------------------------------------- frete das compras

type FreightParams = {
  branch: FinancialBranch;
  issueStart?: string | null;
  issueEnd?: string | null;
  entryStart?: string | null;
  entryEnd?: string | null;
  supplier?: string | null;
  invoiceDocument?: string | null;
  freightDocument?: string | null;
  page?: number;
  pageSize?: number;
  refresh?: boolean;
  signal?: AbortSignal;
};

function freightQuery(params: FreightParams, extra: Record<string, unknown> = {}): string {
  return buildQuery({
    branch: branchParam(params.branch),
    issueStart: params.issueStart,
    issueEnd: params.issueEnd,
    entryStart: params.entryStart,
    entryEnd: params.entryEnd,
    supplier: params.supplier,
    invoiceDocument: params.invoiceDocument,
    freightDocument: params.freightDocument,
    page: params.page,
    pageSize: params.pageSize,
    refresh: params.refresh ? "true" : null,
    ...(extra as Record<string, string | number | boolean | null | undefined>),
  });
}

export function fetchFreightDashboard(
  params: FreightParams & {
    situation?: string | null;
    sortBy?: string | null;
    sortDir?: string | null;
  },
): Promise<FreightDashboardPayload> {
  const query = freightQuery(params, {
    situation: params.situation,
    sortBy: params.sortBy,
    sortDir: params.sortDir,
  });
  return get<FreightDashboardPayload>(
    `/freight/dashboard${query}`,
    "Não foi possível carregar o frete das compras.",
    params.signal,
  );
}

export function fetchFreightInconsistencies(
  params: FreightParams,
): Promise<FreightInconsistenciesPayload> {
  return get<FreightInconsistenciesPayload>(
    `/freight/inconsistencies${freightQuery(params)}`,
    "Não foi possível carregar as inconsistências de frete.",
    params.signal,
  );
}

// ------------------------------------------------------------------ indicadores

type IndicatorParams = {
  branch?: FinancialBranch | null;
  competence?: string | null;
  refresh?: boolean;
  signal?: AbortSignal;
};

export function fetchDepartmentIndicators(
  params: IndicatorParams = {},
): Promise<DepartmentIndicators> {
  const query = buildQuery({
    branch: params.branch ?? null,
    competence: params.competence,
    refresh: params.refresh ? "true" : null,
  });
  return get<DepartmentIndicators>(
    `/indicators/department${query}`,
    "Não foi possível carregar o IDD do Financeiro.",
    params.signal,
  );
}

export function fetchGlobalIndicators(params: IndicatorParams = {}): Promise<GlobalIndicators> {
  const query = buildQuery({
    branch: params.branch ?? null,
    competence: params.competence,
    refresh: params.refresh ? "true" : null,
  });
  return get<GlobalIndicators>(
    `/indicators/global${query}`,
    "Não foi possível carregar o IGD da Delpi.",
    params.signal,
  );
}
