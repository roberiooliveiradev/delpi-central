import type { AuditDetail } from "../api/audit5sApi";
import { SENSOS, sensoName } from "../constants/audit5s";

export type SensoScoreSummary = {
  order: number;
  name: string;
  percentual: number | null;
  scored: number;
  total: number;
};

function roundPercent(value: number): number {
  return Math.round(value * 100) / 100;
}

export function computeSensoSummaries(
  audit: AuditDetail,
  sensoNamesByOrder: Map<number, string>,
): SensoScoreSummary[] {
  const responseByCriterion = new Map(
    audit.responses.map((response) => [response.criterion_id, response]),
  );

  return SENSOS.map(({ order }) => {
    const criteria = audit.criteria.filter((item) => item.senso_order === order);
    const applicableScores: number[] = [];
    let scored = 0;

    for (const criterion of criteria) {
      const response = responseByCriterion.get(criterion.id);
      if (!response) continue;

      if (response.is_not_applicable) {
        scored += 1;
        continue;
      }

      if (response.score != null) {
        scored += 1;
        applicableScores.push(response.score);
      }
    }

    const apiPercentual = audit.scores.sensos.find((item) => item.senso_order === order)?.percentual;
    const computedPercentual =
      applicableScores.length > 0
        ? roundPercent(
            (applicableScores.reduce((sum, score) => sum + score, 0) /
              (applicableScores.length * 5)) *
              100,
          )
        : null;

    return {
      order,
      name: sensoName(order, sensoNamesByOrder.get(order)),
      percentual: apiPercentual ?? computedPercentual,
      scored,
      total: criteria.length,
    };
  });
}

export function scoreTone(percentual: number | null): "empty" | "low" | "mid" | "high" {
  if (percentual == null) return "empty";
  if (percentual >= 80) return "high";
  if (percentual >= 60) return "mid";
  return "low";
}

export function formatPercentual(value: number | null): string {
  if (value == null) return "—";
  return Number.isInteger(value) ? `${value}%` : `${value.toFixed(1)}%`;
}
