export type ScoreStatusVariant = "success" | "warning" | "danger" | "info";

export function getScoreStatusVariant(score: number): ScoreStatusVariant {
  if (score >= 8) return "success";
  if (score >= 7) return "info";
  if (score >= 6) return "warning";
  return "danger";
}
