/** Cliente da BFF — Estoque histórico P7 (R03, consulta operacional). */
import { cfApiUrl, httpGet, httpGetBlob } from "./httpClient";

export type StockInventoryBranch = "all" | "01" | "02";
export type StockInventoryScope = "all_products" | "mp_pi_pa";

export type StockInventoryStatus =
  | "available"
  | "incomplete"
  | "source_missing"
  | "no_matching_items";

export type StockInventoryItem = {
  productCode: string;
  description: string | null;
  productType: string | null;
  productGroup: string | null;
  unit: string | null;
  warehouse: string | null;
  branchCode: string | null;
  historicalQuantity: string;
  historicalStockValue: string;
};

export type StockInventoryTypeSummary = {
  productType: string | null;
  itemCount: number;
  totalQuantity: string;
  totalStockValue: string;
};

export type StockInventoryWarehouseSummary = {
  branchCode: string | null;
  warehouse: string | null;
  itemCount: number;
  totalQuantity: string;
  totalStockValue: string;
};

export type StockInventoryPagination = {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

/** Proveniência do motor P7 (evolução aditiva do contrato — doc 119 §8). */
export type StockInventoryProvenance = {
  engine?: string;
  officialProducer?: string;
  snapshotDate?: string;
  movementCutoff?: string;
  opAliveCutoff?: string;
  processWarehouse?: string;
  reportScope?: string;
  openOrdersAllocated?: number;
};

export type StockInventoryPayload = {
  report: string;
  period: string;
  referenceDate: string;
  dataAsOf: string | null;
  branchCode: string;
  reportScope: string;
  source: string;
  officialP7: boolean;
  parityStatus: string;
  parityNotes?: string[];
  provenance?: StockInventoryProvenance;
  status: StockInventoryStatus;
  branchesAvailable: string[];
  branchesMissing: string[];
  historicalTotal: string | null;
  /** EM ESTOQUE — SB9 fora do armazém de processo (universo do escopo). */
  stockTotal?: string | null;
  /** EM PROCESSO — fatia física do armazém 99 (bloco sem-OP MATR989). */
  processPhysicalTotal?: string | null;
  /** EM PROCESSO — fatia alocada a OPs vivas na emissão (MATR989). */
  processAllocatedTotal?: string | null;
  /** EM PROCESSO total = física + alocada. */
  processTotal?: string | null;
  /** TOTAL GERAL = EM ESTOQUE + EM PROCESSO. */
  grandTotal?: string | null;
  pagination: StockInventoryPagination;
  items: StockInventoryItem[];
  summariesByType: StockInventoryTypeSummary[];
  summariesByWarehouse: StockInventoryWarehouseSummary[];
};

export type StockInventoryQuery = {
  /** Competência YYYY-MM — snapshot no último dia calendário do mês. */
  period: string;
  branch?: StockInventoryBranch;
  reportScope?: StockInventoryScope;
  warehouse?: string;
  page?: number;
  pageSize?: number;
};

type Envelope<T> = { success: boolean; data?: T | null };

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  return search.toString();
}

export async function getStockInventory(
  query: StockInventoryQuery,
  options?: { signal?: AbortSignal },
): Promise<StockInventoryPayload> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    report_scope: query.reportScope ?? "all_products",
    warehouse: query.warehouse,
    page: query.page ?? 1,
    page_size: query.pageSize ?? 50,
  });
  const envelope = await httpGet<Envelope<StockInventoryPayload>>(
    cfApiUrl(`/closing/stock-inventory?${qs}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia da API de estoque histórico.");
  }
  return envelope.data;
}

/** Nome do arquivo exportado — mesmo contrato do servidor (doc 119 §8.C). */
export function stockInventoryExportFilename(
  query: Pick<StockInventoryQuery, "period" | "branch" | "reportScope">,
  format: "csv" | "pdf" = "csv",
): string {
  return (
    `p7-inventory-${query.period}-${query.branch ?? "all"}-` +
    `${query.reportScope ?? "all_products"}.${format}`
  );
}

/**
 * Export do mesmo motor P7 — cabeçalho com competência, filial,
 * escopo, hash de conteúdo e marca de paridade (documento não oficial
 * enquanto a homologação MATR460 estiver pendente).
 */
export async function exportStockInventory(
  query: StockInventoryQuery,
  format: "csv" | "pdf",
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    report_scope: query.reportScope ?? "all_products",
    warehouse: query.warehouse,
    format,
  });
  return httpGetBlob(
    cfApiUrl(`/closing/stock-inventory/export?${qs}`),
    options,
  );
}

/** Alias de compatibilidade — o formato CSV continua o default. */
export async function exportStockInventoryCsv(
  query: StockInventoryQuery,
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  return exportStockInventory(query, "csv", options);
}
