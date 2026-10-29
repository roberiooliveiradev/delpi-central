/** Cliente da BFF — R08 Material em Processo (MATR989, consulta
 *  operacional). */
import { cfApiUrl, httpGet, httpGetBlob } from "./httpClient";
import type {
  StockInventoryBranch,
  StockInventoryPagination,
  StockInventoryScope,
  StockInventoryStatus,
} from "./stockInventoryApi";

export type { StockInventoryBranch, StockInventoryScope };

export type WorkInProcessItem = {
  branchCode: string | null;
  productCode: string;
  description: string | null;
  productType: string | null;
  productionOrder: string | null;
  allocatedQuantity: string;
  allocatedValue: string;
};

export type WorkInProcessTypeSummary = {
  productType: string | null;
  physicalValue: string;
  allocatedValue: string;
  totalValue: string;
  openOrderCount: number;
};

export type WorkInProcessPayload = {
  report: string;
  period: string;
  referenceDate: string;
  dataAsOf: string | null;
  branchCode: string;
  reportScope: string;
  source: string;
  officialMatr989: boolean;
  parityStatus: string;
  parityNotes?: string[];
  provenance?: Record<string, unknown>;
  status: StockInventoryStatus;
  branchesAvailable: string[];
  branchesMissing: string[];
  /** Bloco físico sem-OP do MATR989 — SB9 armazém 99 (operando H02). */
  physicalTotal: string | null;
  /** Saldo líquido alocado a OPs vivas na emissão (RE − DE). */
  allocatedTotal: string | null;
  /** Total MATR989 = físico + alocado. */
  grandTotal: string | null;
  pagination: StockInventoryPagination;
  items: WorkInProcessItem[];
  summariesByType: WorkInProcessTypeSummary[];
};

export type WorkInProcessQuery = {
  period: string;
  branch?: StockInventoryBranch;
  reportScope?: StockInventoryScope;
  warehouse?: string;
  page?: number;
  pageSize?: number;
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

export async function getWorkInProcess(
  query: WorkInProcessQuery,
  options?: { signal?: AbortSignal },
): Promise<WorkInProcessPayload> {
  const qs = buildQuery({
    period: query.period,
    branch: query.branch ?? "all",
    report_scope: query.reportScope ?? "all_products",
    warehouse: query.warehouse,
    page: query.page ?? 1,
    page_size: query.pageSize ?? 50,
  });
  const envelope = await httpGet<Envelope<WorkInProcessPayload>>(
    cfApiUrl(`/closing/work-in-process?${qs}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia da API de material em processo.");
  }
  return envelope.data;
}

export function workInProcessExportFilename(
  query: Pick<WorkInProcessQuery, "period" | "branch" | "reportScope">,
  format: "csv" | "pdf",
): string {
  return (
    `r08-work-in-process-${query.period}-${query.branch ?? "all"}-` +
    `${query.reportScope ?? "all_products"}.${format}`
  );
}

/**
 * Export do mesmo motor MATR989 — metadados de identidade, hash de
 * conteúdo e marca de paridade (documento não oficial enquanto a
 * homologação MATR989 estiver pendente).
 */
export async function exportWorkInProcess(
  query: WorkInProcessQuery,
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
    cfApiUrl(`/closing/work-in-process/export?${qs}`),
    options,
  );
}
