/** Cliente da BFF — Baixas financeiras (R01/R02, Central de Fechamento). */
import { cfApiUrl, httpGet } from "./httpClient";

export type SettlementSide = "payable" | "receivable";

export type SettlementItem = {
  settlementId: string;
  settlementDate: string | null;
  settlementAmount: string;
  currencyCode: string | null;
  natureCode: string | null;
  natureDescription: string | null;
  documentNumber: string | null;
  prefix: string | null;
  installment: string | null;
  documentType: string | null;
  partyCode: string | null;
  partyStore: string | null;
  partyName: string | null;
  issueDate: string | null;
  dueDate: string | null;
  history: string | null;
  movementType: string | null;
  paymentDirection: string | null;
  branchCode: string | null;
  branchResolution: string;
  linkStatus: string;
};

export type SettlementQuality = {
  missingDocumentCount: number;
  missingNatureCount: number;
  unresolvedBranchCount: number;
};

export type SettlementsPagination = {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

export type SettlementsListPayload = {
  report: string;
  side: SettlementSide;
  period: { start_date: string; end_date: string };
  status: string;
  officialTotals: boolean;
  quality: SettlementQuality;
  pagination: SettlementsPagination;
  sort: { sort_by: string; sort_dir: string };
  items: SettlementItem[];
};

export type SettlementSummaryGroup = {
  side: string;
  currencyCode: string | null;
  natureCode: string | null;
  natureDescription: string | null;
  movementType: string | null;
  eventCount: number;
  totalAmount: string;
};

export type SettlementsSummaryPayload = {
  report: string;
  period: { start_date: string; end_date: string };
  status: string;
  officialTotals: boolean;
  quality: SettlementQuality;
  groups: SettlementSummaryGroup[];
};

type Envelope<T> = { success: boolean; data?: T | null };

export type SettlementsQuery = {
  side: SettlementSide;
  startDate: string;
  endDate: string;
  natureCode?: string;
  movementType?: string;
  sortBy?: string;
  sortDir?: "asc" | "desc";
  page?: number;
  pageSize?: number;
};

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  return search.toString();
}

export async function getFinancialSettlements(
  query: SettlementsQuery,
  options?: { signal?: AbortSignal },
): Promise<SettlementsListPayload> {
  const qs = buildQuery({
    side: query.side,
    start_date: query.startDate,
    end_date: query.endDate,
    nature_code: query.natureCode,
    movement_type: query.movementType,
    sort_by: query.sortBy ?? "settlement_date",
    sort_dir: query.sortDir ?? "desc",
    page: query.page ?? 1,
    page_size: query.pageSize ?? 50,
  });
  const envelope = await httpGet<Envelope<SettlementsListPayload>>(
    cfApiUrl(`/closing/financial-settlements?${qs}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia da API de baixas financeiras.");
  }
  return envelope.data;
}

export async function getFinancialSettlementsSummary(
  query: Omit<SettlementsQuery, "side" | "page" | "pageSize" | "sortBy" | "sortDir">,
  options?: { signal?: AbortSignal },
): Promise<SettlementsSummaryPayload> {
  const qs = buildQuery({
    start_date: query.startDate,
    end_date: query.endDate,
    nature_code: query.natureCode,
    movement_type: query.movementType,
  });
  const envelope = await httpGet<Envelope<SettlementsSummaryPayload>>(
    cfApiUrl(`/closing/financial-settlements/summary?${qs}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia da API de resumo de baixas.");
  }
  return envelope.data;
}
