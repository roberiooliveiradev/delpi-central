import type { KpiBlock } from "../types";

export type KpiGoalDirection = "higher_is_better" | "lower_is_better";

export type KpiComparisonTone = "positive" | "negative";

export function resolveKpiComparisonTone(
  block: KpiBlock | undefined,
  direction: KpiGoalDirection,
): KpiComparisonTone | undefined {
  if (!block?.available) return undefined;

  const target = block.target;
  const value = block.value;
  if (target == null || value == null || target <= 0) return undefined;

  const onTrack =
    direction === "lower_is_better" ? value <= target : value >= target;

  return onTrack ? "positive" : "negative";
}
