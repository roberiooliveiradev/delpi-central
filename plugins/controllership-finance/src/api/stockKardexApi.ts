/** Cliente da BFF — R06 Kardex/CPV e R07 Ajustes de Inventário
 * (regra MATR910, consulta operacional — doc 122, IMPLEMENTATION-015). */
import { cfApiUrl, httpGet, httpGetBlob } from "./httpClient";
import type {
  StockInventoryBranch,
  StockInventoryStatus,
} from "./stockInventoryApi";

export type { StockInventoryBranch };

export type KardexMovementItem = {
  sourceTable: string;
  movementId: number;
  branchCode: string;
  warehouse: string;
  productCode: string;
  description: string;
  productType: string | null;
  unit: string | null;
  document: string;
  series: string | null;
  movementDate: string;
  sequence: string | null;
  tm: string | null;
  cf: string | null;
  reference: string | null;
  movementKind: "entry" | "output" | string;
  isReturn: boolean;
  documentType: string | null;
  entryQuantity: string;
  entryValue: string;
  outputQuantity: string;
  outputValue: string;
  unitCost: string | null;
  costAsOfSource: string;
  runningQuantity: string | null;
  runningValue: string | null;
};

export type KardexTotals = {
  movementCount: number;
  blockCount: number;
  entryQuantity: string;
  entryValue: string;
  outputQuantity: string;
  outputValue: string;
  netQuantity: string;
  netValue: string;
  openingValue: string | null;
  closingValue: string | null;
};

export type KardexPagination = {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
};

export type KardexPayload = {
  report: "stock-kardex" | "inventory-adjustments" | string;
  period: string;
  referenceDate: string;
  dataAsOf: string | null;
  branchCode: string;
  warehouse?: string | null;
  documentKind: string;
  status: StockInventoryStatus;
  branchesAvailable: string[];
  branchesMissing: string[];
  totals: KardexTotals;
  items: KardexMovementItem[];
  blocks?: Record<string, unknown>[];
  pagination?: KardexPagination;
  parityStatus: string;
  parityNotes?: string[];
  provenance?: Record<string, unknown>;
};

export type KardexGroupSummary = {
  productType?: string | null;
  branchCode?: string;
  warehouse?: string;
  movementCount: number;
  entryQuantity: string;
  entryValue: string;
  outputQuantity: string;
  outputValue: string;
};

export type KardexTopProduct = {
  productCode: string;
  description: string | null;
  movementCount: number;
  outputQuantity: string;
  outputValue: string;
};

export type KardexSummaryPayload = {
  report: string;
  period: string;
  status: StockInventoryStatus;
  totals: KardexTotals;
  summariesByType: KardexGroupSummary[];
  summariesByWarehouse: KardexGroupSummary[];
  topProductsByCost: KardexTopProduct[];
  parityStatus: string;
  parityNotes?: string[];
  provenance?: Record<string, unknown>;
};

export type CpvPayload = {
  report: "cpv";
  period: string;
  referenceDate: string;
  branchCode: string;
  source: string;
  officialR06: boolean;
  asOfConvention: "live" | string;
  cfops: string[];
  status: StockInventoryStatus;
  summary: {
    cpvTotal: string;
    totalMovements: number;
    totalQuantity: string;
    averageCostPerMovement: string;
    averageCostPerUnit: string;
    firstMovementDate: string;
    lastMovementDate: string;
  };
  byCfop: {
    cfop: string;
    totalMovements: number;
    totalQuantity: string;
    cpvTotal: string;
  }[];
  byTm: {
    tm: string;
    cfop: string;
    tesDescription: string | null;
    totalMovements: number;
    totalQuantity: string;
    cpvTotal: string;
  }[];
  topProducts: {
    productCode: string;
    description: string | null;
    totalMovements: number;
    totalQuantity: string;
    cpvTotal: string;
  }[];
  topDocuments: {
    document: string;
    totalMovements: number;
    totalQuantity: string;
    cpvTotal: string;
  }[];
  parityStatus: string;
  parityNotes?: string[];
  provenance?: Record<string, unknown>;
};

export type StockKardexQuery = {
  period: string;
  branch?: StockInventoryBranch;
  warehouse?: string;
  productCode?: string;
  productType?: string;
  movementKind?: "entry" | "output";
  page?: number;
  pageSize?: number;
  sort?: "date" | "product";
  sortDir?: "asc" | "desc";
};

export type InventoryAdjustmentsQuery = Omit<
  StockKardexQuery,
  "productType" | "sort" | "sortDir"
>;

type Envelope<T> = { success: boolean; data?: T | null };

function buildQuery(
  params: Record<string, string | number | undefined>,
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

export async function getStockKardex(
  query: StockKardexQuery,
  options?: { signal?: AbortSignal },
): Promise<KardexPayload> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    warehouse: query.warehouse,
    product_code: query.productCode,
    product_type: query.productType,
    movement_kind: query.movementKind,
    page: query.page ?? 1,
    page_size: query.pageSize ?? 50,
    sort: query.sort ?? "date",
    sort_dir: query.sortDir ?? "asc",
  });
  return getData<KardexPayload>(
    `/closing/stock-kardex?${qs}`,
    options,
    "Resposta vazia da API de kardex.",
  );
}

export async function getStockKardexSummary(
  query: StockKardexQuery,
  options?: { signal?: AbortSignal },
): Promise<KardexSummaryPayload> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    warehouse: query.warehouse,
    product_code: query.productCode,
    product_type: query.productType,
  });
  return getData<KardexSummaryPayload>(
    `/closing/stock-kardex/summary?${qs}`,
    options,
    "Resposta vazia da API de resumo do kardex.",
  );
}

export async function getInventoryAdjustments(
  query: InventoryAdjustmentsQuery,
  options?: { signal?: AbortSignal },
): Promise<KardexPayload> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    warehouse: query.warehouse,
    product_code: query.productCode,
    movement_kind: query.movementKind,
    page: query.page ?? 1,
    page_size: query.pageSize ?? 50,
  });
  return getData<KardexPayload>(
    `/closing/inventory-adjustments?${qs}`,
    options,
    "Resposta vazia da API de ajustes de inventário.",
  );
}

export async function getInventoryAdjustmentsSummary(
  query: InventoryAdjustmentsQuery,
  options?: { signal?: AbortSignal },
): Promise<KardexSummaryPayload> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    warehouse: query.warehouse,
    product_code: query.productCode,
  });
  return getData<KardexSummaryPayload>(
    `/closing/inventory-adjustments/summary?${qs}`,
    options,
    "Resposta vazia da API de resumo de ajustes.",
  );
}

export async function getCpv(
  query: { period: string; branch?: StockInventoryBranch; topLimit?: number },
  options?: { signal?: AbortSignal },
): Promise<CpvPayload> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    top_limit: query.topLimit ?? 10,
  });
  return getData<CpvPayload>(
    `/closing/cpv?${qs}`,
    options,
    "Resposta vazia da API de CPV.",
  );
}

export function kardexExportFilename(
  report: string,
  query: { period: string; branch?: StockInventoryBranch },
  format: "csv" | "pdf",
): string {
  return `${report}-${query.period}-${query.branch ?? "all"}.${format}`;
}

/** Export R06/R07 — mesmo motor da consulta; o arquivo declara
 *  competência, filial, armazém, data-base, fonte, hash e marca de
 *  paridade pendente (documento operacional, não oficial). */
export async function exportStockKardex(
  query: StockKardexQuery,
  format: "csv" | "pdf",
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    warehouse: query.warehouse,
    product_code: query.productCode,
    product_type: query.productType,
    format,
  });
  return httpGetBlob(
    cfApiUrl(`/closing/stock-kardex/export?${qs}`),
    options,
  );
}

export async function exportInventoryAdjustments(
  query: InventoryAdjustmentsQuery,
  format: "csv" | "pdf",
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    warehouse: query.warehouse,
    product_code: query.productCode,
    format,
  });
  return httpGetBlob(
    cfApiUrl(`/closing/inventory-adjustments/export?${qs}`),
    options,
  );
}
