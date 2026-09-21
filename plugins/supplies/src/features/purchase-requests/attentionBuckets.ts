import type { OverallStage } from "./types";

/** Mirrors purchase-requests ATTENTION_BUCKETS. The owner counts; this only writes the URL. */
export const ATTENTION_BUCKETS = {
  ordering: ["awaiting_order", "partially_ordered"],
  receiving: ["ordered", "awaiting_receipt", "partially_received"],
  completed: ["completed", "residual_closed"],
} as const satisfies Record<string, readonly OverallStage[]>;

export type AttentionBucketId = "all" | keyof typeof ATTENTION_BUCKETS;

function sameStages(left: readonly string[], right: readonly string[]): boolean {
  if (left.length !== right.length) return false;
  const pending = [...right];
  return left.every((stage) => {
    const index = pending.indexOf(stage);
    if (index < 0) return false;
    pending.splice(index, 1);
    return true;
  });
}

export function activeAttentionBucket(stages: readonly OverallStage[]): AttentionBucketId | null {
  if (stages.length === 0) return "all";
  const entries = Object.entries(ATTENTION_BUCKETS) as Array<
    [keyof typeof ATTENTION_BUCKETS, readonly OverallStage[]]
  >;
  for (const [id, expected] of entries) {
    if (sameStages(stages, expected)) return id;
  }
  return null;
}

export function attentionQueryPatch(bucket: AttentionBucketId): {
  overall_stages: OverallStage[];
  page: number;
} {
  if (bucket === "all") return { overall_stages: [], page: 1 };
  return { overall_stages: [...ATTENTION_BUCKETS[bucket]], page: 1 };
}
