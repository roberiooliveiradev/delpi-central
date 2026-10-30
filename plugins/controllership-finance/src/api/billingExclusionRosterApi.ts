/** Cliente da BFF — R11 Notas Fiscais a Desconsiderar
 *  (lista investigativa SD2/D2_EMISSAO — critério histórico observado
 *  grupo 9035 ∩ TES 594, doc 126, IMPLEMENTATION-STAGE-02).
 *  Nenhuma nota é excluída automaticamente de CPV, faturamento ou DRE. */
import { cfApiUrl, httpGet, httpGetBlob } from "./httpClient";
import type { StockInventoryBranch } from "./stockInventoryApi";

export type { StockInventoryBranch };

export type BillingExclusionView =
  | "candidates"
  | "out_of_criteria"
  | "all";

export type BillingExclusionItem = {
  lineId: number;
  branchCode: string;
  document: string;
  series: string | null;
  item: string | null;
  productCode: string;
  productDescription: string | null;
  productType: string | null;
  productGroup: string | null;
  tes: string | null;
  tesDescription: string | null;
  cf: string | null;
  customerCode: string | null;
  customerStore: string | null;
  customerName: string | null;
  accountCode: string | null;
  warehouse: string | null;
  orderNumber: string | null;
  issueDate: string;
  quantity: string;
  unitPrice: string;
  totalValue: string;
  stockCost: string;
  tesStockMovement: string | null;
  tesDuplicateFlag: string | null;
  documentItemCount: number;
  hasStockSiblingItem: boolean;
  selectionStatus: string;
  costStatus: string;
  findings: string[];
};

export type BillingExclusionFinding = {
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

export type BillingExclusionSummary = {
  totalValue: string;
  lineCount: number;
  documentCount: number;
  customerCount: number;
  zeroCostCount: number;
  missingStockSiblingDocumentCount: number;
  findingCount: number;
  candidateLineCount: number;
  outOfCriteriaLineCount: number;
  byTes: {
    tes: string;
    lineCount: number;
    totalValue: string;
  }[];
  byProductGroup: {
    productGroup: string;
    lineCount: number;
    totalValue: string;
  }[];
};

export type BillingExclusionRule = {
  ruleId: string;
  description: string;
  implemented: boolean;
  pendingReason?: string;
  limitation?: string;
  kind?: string;
  note?: string;
  expressedAs?: string;
  evidenceRefs?: string[];
};

export type BillingExclusionPayload = {
  report: "billing-exclusion-roster" | string;
  reportId: string;
  period: string;
  branchCode: string;
  view: BillingExclusionView;
  status: string;
  selection: {
    axis: string;
    grain: string;
    observedCriteria?: { productGroup: string; tes: string };
    view?: string;
    viewSemantics?: string;
    predicateOfficiality?: string;
    affectedCalculation?: string;
    historicalBaseline?: Record<string, unknown>;
  };
  pagination?: {
    page: number;
    page_size: number;
    total_items: number;
    population_items: number;
  };
  summary: BillingExclusionSummary | null;
  findings: BillingExclusionFinding[];
  findingsTruncated: boolean;
  rulesCatalog: BillingExclusionRule[];
  items: BillingExclusionItem[];
  parityStatus: string;
  parityNotes?: string[];
  provenance?: Record<string, unknown>;
};

export type BillingExclusionQuery = {
  period: string;
  branch?: StockInventoryBranch;
  view?: BillingExclusionView;
  productGroup?: string;
  productCode?: string;
  document?: string;
  customerCode?: string;
  tes?: string;
  page?: number;
  pageSize?: number;
  sort?: "date" | "document" | "product" | "total_value";
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

export async function getBillingExclusionRoster(
  query: BillingExclusionQuery,
  options?: { signal?: AbortSignal },
): Promise<BillingExclusionPayload> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    view: query.view ?? "candidates",
    product_group: query.productGroup,
    product_code: query.productCode,
    document: query.document,
    customer_code: query.customerCode,
    tes: query.tes,
    include_findings: true,
    page: query.page ?? 1,
    page_size: query.pageSize ?? 50,
    sort: query.sort ?? "date",
    sort_dir: query.sortDir ?? "asc",
  });
  return getData<BillingExclusionPayload>(
    `/closing/billing-exclusion-roster?${qs}`,
    options,
    "Resposta vazia da API de notas fiscais a desconsiderar.",
  );
}

export function billingExclusionExportFilename(
  query: { period: string; branch?: StockInventoryBranch; view?: BillingExclusionView },
  format: "csv" | "pdf",
): string {
  return `billing-exclusion-roster-${query.period}-${query.branch ?? "all"}-${query.view ?? "candidates"}.${format}`;
}

/** Export R11 — mesmo motor da consulta; o arquivo declara competência,
 *  filial, visão, critério observado, caráter investigativo, fonte,
 *  hash e marca de paridade pendente. */
export async function exportBillingExclusionRoster(
  query: BillingExclusionQuery,
  format: "csv" | "pdf",
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    view: query.view ?? "candidates",
    product_group: query.productGroup,
    product_code: query.productCode,
    document: query.document,
    customer_code: query.customerCode,
    tes: query.tes,
    format,
  });
  return httpGetBlob(
    cfApiUrl(`/closing/billing-exclusion-roster/export?${qs}`),
    options,
  );
}
