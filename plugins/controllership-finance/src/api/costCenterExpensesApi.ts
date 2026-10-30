/** Cliente da BFF — R10 Despesas por Centro de Custo
 *  (seleção histórica SD1/D1_DTDIGIT + universo investigativo,
 *  doc 126, IMPLEMENTATION-STAGE-01). */
import { cfApiUrl, httpGet, httpGetBlob } from "./httpClient";
import type { StockInventoryBranch } from "./stockInventoryApi";

export type { StockInventoryBranch };

export type CostCenterExpensesUniverse = "calculation" | "investigation";
export type CostCenterExpensesView =
  | "all"
  | "divergences"
  | "unclassified";

export type CostCenterExpenseItem = {
  lineId: number;
  branchCode: string;
  document: string;
  series: string | null;
  item: string | null;
  sequence: string | null;
  productCode: string;
  productDescription: string | null;
  productType: string | null;
  productGroup: string | null;
  documentType: string | null;
  costCenter: string | null;
  costCenterDescription: string | null;
  costCenterCatalogStatus: string;
  accountCode: string | null;
  tes: string | null;
  cf: string | null;
  supplierCode: string | null;
  supplierStore: string | null;
  supplierName: string | null;
  warehouse: string | null;
  orderNumber: string | null;
  entryDate: string;
  issueDate: string | null;
  quantity: string;
  unitValue: string;
  totalValue: string;
  universe: CostCenterExpensesUniverse;
  calculationExclusion: string | null;
  costClass: string;
  findings: string[];
};

export type CostCenterExpenseFinding = {
  reportId: string;
  findingId: string;
  ruleId: string;
  status: string;
  lineId: number;
  sourceRecord: Record<string, unknown>;
  observedValues: Record<string, unknown>;
  findingExplanation: string;
  evidenceRefs: string[];
  erpReviewGuidance: string;
};

export type CostCenterExpensesSummary = {
  totalValue: string;
  lineCount: number;
  documentCount: number;
  costCenterCount: number;
  supplierCount: number;
  findingCount: number;
  unclassifiedCount: number;
  byCostCenter: {
    costCenter: string | null;
    costCenterDescription?: string | null;
    lineCount: number;
    totalValue: string;
    findingCount: number;
  }[];
  byProductType: {
    productType: string;
    lineCount: number;
    totalValue: string;
  }[];
};

export type CostCenterExpensesRule = {
  ruleId: string;
  description: string;
  implemented: boolean;
  pendingReason?: string;
  limitation?: string;
  universe?: string;
  kind?: string;
  note?: string;
  evidenceRefs?: string[];
};

export type CostCenterExpensesPayload = {
  report: "cost-center-expenses" | string;
  reportId: string;
  period: string;
  branchCode: string;
  universe: CostCenterExpensesUniverse;
  view: CostCenterExpensesView;
  status: string;
  selection: {
    axis: string;
    grain: string;
    excludedTes: string[];
    excludeMp: boolean;
    excludeBenefits: boolean;
    universeSemantics?: string;
    historicalBaseline?: Record<string, unknown>;
  };
  pagination?: {
    page: number;
    page_size: number;
    total_items: number;
    universe_items: number;
  };
  summary: CostCenterExpensesSummary | null;
  findings: CostCenterExpenseFinding[];
  findingsTruncated: boolean;
  rulesCatalog: CostCenterExpensesRule[];
  items: CostCenterExpenseItem[];
  parityStatus: string;
  parityNotes?: string[];
  provenance?: Record<string, unknown>;
};

export type CostCenterExpensesQuery = {
  period: string;
  branch?: StockInventoryBranch;
  universe?: CostCenterExpensesUniverse;
  view?: CostCenterExpensesView;
  costCenter?: string;
  productCode?: string;
  document?: string;
  supplierCode?: string;
  tes?: string;
  page?: number;
  pageSize?: number;
  sort?: "date" | "document" | "cost_center" | "product" | "total_value";
  sortDir?: "asc" | "desc";
};

type Envelope<T> = { success: boolean; data?: T | null };

function buildQuery(
  params: Record<string, string | number | boolean | undefined>,
): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  return search.toString();
}

async function getData<T>(
  path: string,
  options?: { signal?: AbortSignal },
  emptyError = "Resposta vazia da API.",
): Promise<T> {
  const envelope = await httpGet<Envelope<T>>(cfApiUrl(path), options);
  if (!envelope?.data) {
    throw new Error(emptyError);
  }
  return envelope.data;
}

export async function getCostCenterExpenses(
  query: CostCenterExpensesQuery,
  options?: { signal?: AbortSignal },
): Promise<CostCenterExpensesPayload> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    universe: query.universe ?? "calculation",
    view: query.view ?? "all",
    cost_center: query.costCenter,
    product_code: query.productCode,
    document: query.document,
    supplier_code: query.supplierCode,
    tes: query.tes,
    include_findings: true,
    page: query.page ?? 1,
    page_size: query.pageSize ?? 50,
    sort: query.sort ?? "date",
    sort_dir: query.sortDir ?? "asc",
  });
  return getData<CostCenterExpensesPayload>(
    `/closing/cost-center-expenses?${qs}`,
    options,
    "Resposta vazia da API de despesas por centro de custo.",
  );
}

export function costCenterExpensesExportFilename(
  query: { period: string; branch?: StockInventoryBranch; universe?: CostCenterExpensesUniverse },
  format: "csv" | "pdf",
): string {
  return `cost-center-expenses-${query.period}-${query.branch ?? "all"}-${query.universe ?? "calculation"}.${format}`;
}

/** Export R10 — mesmo motor da consulta; o arquivo declara competência,
 *  filial, universo (apuração ou investigação — nunca somados), critérios
 *  de seleção, fonte, hash e marca de paridade pendente. */
export async function exportCostCenterExpenses(
  query: CostCenterExpensesQuery,
  format: "csv" | "pdf",
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    universe: query.universe ?? "calculation",
    view: query.view ?? "all",
    cost_center: query.costCenter,
    product_code: query.productCode,
    document: query.document,
    supplier_code: query.supplierCode,
    tes: query.tes,
    format,
  });
  return httpGetBlob(
    cfApiUrl(`/closing/cost-center-expenses/export?${qs}`),
    options,
  );
}
