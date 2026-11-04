/** Cliente da BFF — visão operacional R09 Faturamento × MOD (doc 143/144).
 *
 * `GET /closing/competences/{period}/billing-mod-breakdown` — âncoras PA
 * faturadas (SD2/SF4), estrutura SG1 compartilhada, roteiro congelado
 * SHY (última OP) com fallback SG2, recurso → item MOD. Ausências tipadas
 * nunca são zero; paridade oficial pendente (DR-3).
 */
import { cfApiUrl, httpGet } from "./httpClient";

export type TypedNumber = {
  value: number | null;
  state: string;
  /** Motivo/proveniência da ausência, quando produzidos (DR-2). */
  reason?: string;
  detail?: string;
};

export type BillingModLine = {
  level: string;
  product?: string | null;
  productDescription?: string | null;
  operation?: string | null;
  operationDescription?: string | null;
  resource?: string | null;
  modItem?: string | null;
  modDescription?: string | null;
  modUnit?: string | null;
  propagatedQty?: number | null;
  stdTime?: TypedNumber;
  sourceOp?: string | null;
  hours?: TypedNumber;
  costUnit?: TypedNumber;
  costTotal?: TypedNumber;
  costProduct?: TypedNumber;
};

export type BillingModAnchor = {
  branch?: string | null;
  product: string;
  productDescription?: string | null;
  billedQty?: number | null;
  modLines: BillingModLine[];
  sourceMissing?: string[];
};

export type ParityEvidence = {
  scope: {
    referencePeriod: string;
    branches: string[];
    artifact: string;
    measuredAt: string;
    gate: string;
    homologationStatus: string;
  };
  metrics: {
    artifactLines: number;
    calculatedLines: number;
    matchedKeys: number;
    keyCoveragePct: number;
    qtdFatCorrectPct: number;
    stdTimeCorrectPct: number;
    hoursCorrectPct: number;
    missingLines: number;
    extraLines: number;
  };
  semantics: string;
};

export type BillingModBreakdownPayload = {
  report: string;
  reportId?: string;
  period: string;
  branch: string;
  anchors: BillingModAnchor[];
  limitations: string[];
  provenance?: Record<string, unknown>;
  officiality?: string;
  officialParity?: string;
  parityEvidence?: ParityEvidence;
  sourceMissing?: string[];
};

type CfEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
  meta?: Record<string, unknown>;
};

export function getBillingModBreakdown(
  period: string,
  branch: string = "all",
): Promise<BillingModBreakdownPayload> {
  const params = new URLSearchParams({ branch });
  return httpGet<CfEnvelope<BillingModBreakdownPayload>>(
    cfApiUrl(
      `/closing/competences/${encodeURIComponent(
        period,
      )}/billing-mod-breakdown?${params.toString()}`,
    ),
  ).then((envelope) => envelope.data);
}
