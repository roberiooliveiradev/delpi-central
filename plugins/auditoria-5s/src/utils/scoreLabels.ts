const SCORE_LABELS: Record<number, string> = {
  1: "Ruim",
  3: "Médio",
  5: "Bom",
};

export function getScoreSummaryLabel(
  score: number | null | undefined,
  isNotApplicable: boolean,
): string | null {
  if (isNotApplicable) return "N/A";
  if (score != null && SCORE_LABELS[score]) {
    return SCORE_LABELS[score];
  }
  return null;
}
