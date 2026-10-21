/** Cliente da BFF — Estoque histórico P7 (R03, consulta operacional). */
import { cfApiUrl, httpGet } from "./httpClient";

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
  status: StockInventoryStatus;
  branchesAvailable: string[];
  branchesMissing: string[];
  historicalTotal: string | null;
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
