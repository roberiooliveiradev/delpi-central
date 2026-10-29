/** Cliente da BFF — conciliação analítica de estoque.
 *
 * `DIVERGENCIA = ENTRADAS_SAIDAS − P7 − H02` (doc 15.1) computada pela
 * BFF a partir dos três relatórios operacionais — superfície analítica
 * distinta da conciliação governada P3 (nunca persiste registro nem
 * converte fonte ausente em zero).
 */
import { cfApiUrl, httpGet } from "./httpClient";
import type {
  StockInventoryBranch,
  StockInventoryScope,
} from "./stockInventoryApi";

export type { StockInventoryBranch, StockInventoryScope };

export type ReconciliationOperand = {
  available: boolean;
  status: string | null;
  errorCode: string | null;
  value: string | null;
  dataAsOf: string | null;
  parityStatus?: string | null;
};

export type StockReconciliationPayload = {
  report: string;
  kind: "analytical";
  governedReconciliation: string;
  period: string;
  branchCode: string;
  reportScope: string;
  equation: string;
  operandSemantics: Record<string, string>;
  eligibility: "ELIGIBLE" | "INELIGIBLE";
  ineligibleOperands: string[];
  operands: {
    entradasSaidas: ReconciliationOperand;
    p7: ReconciliationOperand;
    h02: ReconciliationOperand;
  };
  components: Record<string, string | null>;
  divergence: string | null;
  divergenceCents: string | null;
  parity: "EXACT_PARITY" | "DIVERGENCE" | "NOT_COMPUTED";
  parityTolerance: string;
  provenance: Record<string, unknown>;
  parityNotes?: string[];
};

export type StockReconciliationQuery = {
  period: string;
  branch?: StockInventoryBranch;
  reportScope?: StockInventoryScope;
};

type Envelope<T> = { success: boolean; data?: T | null };

export async function getStockReconciliation(
  query: StockReconciliationQuery,
  options?: { signal?: AbortSignal },
): Promise<StockReconciliationPayload> {
  const search = new URLSearchParams({
    period: query.period,
    branch: query.branch ?? "all",
    report_scope: query.reportScope ?? "all_products",
  });
  const envelope = await httpGet<Envelope<StockReconciliationPayload>>(
    cfApiUrl(`/closing/analytics/stock-reconciliation?${search}`),
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia da API de conciliação analítica.");
  }
  return envelope.data;
}
