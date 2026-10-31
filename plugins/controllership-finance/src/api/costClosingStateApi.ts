/** Cliente da BFF — projeção governada de estado R12/R15 (doc 129).
 *
 * `GET /closing/competences/{period}/cost-closing-state` — marcadores
 * técnicos observados (SB9010, SX6 `MV_ULMES`, janelas TTAT). Estado,
 * nunca medida: não há homologação nem confirmação de execução ERP.
 */
import { cfApiUrl, httpGet } from "./httpClient";

export type ClosingStateNodeState =
  | "available"
  | "missing"
  | "partial"
  | "observed"
  | "not_advanced"
  | "unavailable"
  | "not_informed";

export type ClosingStateNode = {
  state: ClosingStateNodeState;
  evidenceRefs: Record<string, unknown>;
  limitations: string[];
};

export type ClosingStateBranch = {
  snapshot: ClosingStateNode;
  cutoff_marker: ClosingStateNode;
  cost_evidence: ClosingStateNode;
  wizard_lifecycle: ClosingStateNode;
  human_acceptance: ClosingStateNode;
};

export type CostClosingStatePayload = {
  report: string;
  period: string;
  referenceDate: string | null;
  officiality: string;
  observedAt: string | null;
  evidenceWindow?: { start: string; end: string };
  provenance?: Record<string, unknown>;
  branches: Record<string, ClosingStateBranch>;
  limitations: string[];
};

export function getCostClosingState(
  period: string,
  branch: string = "all",
): Promise<CostClosingStatePayload> {
  const params = new URLSearchParams({ branch });
  return httpGet<CostClosingStatePayload>(
    cfApiUrl(
      `/closing/competences/${encodeURIComponent(
        period,
      )}/cost-closing-state?${params.toString()}`,
    ),
  );
}
