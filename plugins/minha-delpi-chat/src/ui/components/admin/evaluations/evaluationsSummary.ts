import type { AdminResponseEvaluationSummary } from "../../../../data/api/adminTypes";

export function formatEvaluationAverage(score: number | null | undefined): string {
  if (typeof score !== "number" || Number.isNaN(score)) {
    return "—";
  }

  return score.toFixed(1);
}

export function formatHelpfulRate(rate: number | null | undefined): string {
  if (typeof rate !== "number" || Number.isNaN(rate)) {
    return "—";
  }

  return `${Math.round(rate * 100)}%`;
}

export function formatEvaluationCount(value: number | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

export type EvaluationsSummaryView = {
  total: string;
  averageScore: string;
  helpfulRate: string;
  recent24h: string;
};

export function buildEvaluationsSummaryView(
  summary: AdminResponseEvaluationSummary | null | undefined,
): EvaluationsSummaryView {
  if (!summary) {
    return {
      total: "—",
      averageScore: "—",
      helpfulRate: "—",
      recent24h: "—",
    };
  }

  return {
    total: formatEvaluationCount(summary.total),
    averageScore: formatEvaluationAverage(summary.averageScore),
    helpfulRate: formatHelpfulRate(summary.helpfulRate),
    recent24h: formatEvaluationCount(summary.recent24h),
  };
}
