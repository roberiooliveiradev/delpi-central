/** Cliente da BFF — R05 Entradas e Saídas (MATR320, consulta operacional). */
import { cfApiUrl, httpGet, httpGetBlob } from "./httpClient";
import type {
  StockInventoryBranch,
  StockInventoryScope,
  StockInventoryStatus,
} from "./stockInventoryApi";

export type { StockInventoryBranch, StockInventoryScope };

export type StockMovementsTypeRow = {
  productType: string | null;
  openingBalance: string | null;
  purchases: string;
  internalMovements: string;
  productionRequisitions: string;
  transfers: string;
  production: string;
  sales: string;
  processTransfersMemo: string;
  salesReturns: string;
  purchaseReturns: string;
  thirdPartyIn: string;
  thirdPartyOut: string;
  closingBalance: string | null;
  netMovement: string | null;
};

export type StockMovementsTotals = {
  openingBalance?: string | null;
  closingBalance?: string | null;
  netMovement?: string | null;
  [key: string]: string | null | undefined;
};

export type StockMovementsPayload = {
  report: string;
  period: string;
  referenceDate: string;
  dataAsOf: string | null;
  branchCode: string;
  reportScope: string;
  source: string;
  officialMatr320: boolean;
  parityStatus: string;
  parityNotes?: string[];
  provenance?: Record<string, unknown>;
  status: StockInventoryStatus;
  branchesAvailable: string[];
  branchesMissing: string[];
  rows: StockMovementsTypeRow[];
  totals: StockMovementsTotals;
};

export type StockMovementsQuery = {
  period: string;
  branch?: StockInventoryBranch;
  reportScope?: StockInventoryScope;
};

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

export async function getStockMovements(
  query: StockMovementsQuery,
  options?: { signal?: AbortSignal },
): Promise<StockMovementsPayload> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    report_scope: query.reportScope ?? "all_products",
  });
  const envelope = await httpGet<Envelope<StockMovementsPayload>>(
    cfApiUrl(`/closing/stock-movements?${qs}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia da API de entradas e saídas.");
  }
  return envelope.data;
}

/** Nome do arquivo exportado — mesmo contrato do servidor. */
export function stockMovementsExportFilename(
  query: Pick<StockMovementsQuery, "period" | "branch" | "reportScope">,
  format: "csv" | "pdf",
): string {
  return (
    `r05-stock-movements-${query.period}-${query.branch ?? "all"}-` +
    `${query.reportScope ?? "all_products"}.${format}`
  );
}

/**
 * Export do mesmo motor R05 — cabeçalho com competência, filial,
 * escopo, data-base, fonte, hash do conteúdo e marca de paridade
 * (documento não oficial enquanto a homologação MATR320 estiver
 * pendente).
 */
export async function exportStockMovements(
  query: StockMovementsQuery,
  format: "csv" | "pdf",
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    report_scope: query.reportScope ?? "all_products",
    format,
  });
  return httpGetBlob(
    cfApiUrl(`/closing/stock-movements/export?${qs}`),
    options,
  );
}
