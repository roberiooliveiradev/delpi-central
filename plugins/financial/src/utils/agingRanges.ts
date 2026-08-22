/** Ordem canônica das faixas — igual ao catálogo do BFF. */
export const AGING_RANGE_ORDER = [
  "EM_DIA",
  "ATRASO_1_A_5_DIAS",
  "ATRASO_6_A_15_DIAS",
  "ATRASO_16_A_30_DIAS",
  "ATRASO_ACIMA_30_DIAS",
] as const;

/** Ponto médio (dias) de cada faixa para estimar o atraso médio quando a API não envia o KPI. */
const AGING_RANGE_MIDPOINT_DAYS: Record<string, number> = {
  ATRASO_1_A_5_DIAS: 3,
  ATRASO_6_A_15_DIAS: 10.5,
  ATRASO_16_A_30_DIAS: 23,
  ATRASO_ACIMA_30_DIAS: 45,
};

export type AgingRangeCode = (typeof AGING_RANGE_ORDER)[number];

export function sortAgingByOrder<T extends { code: string; order?: number }>(items: readonly T[]): T[] {
  return [...items].sort((left, right) => {
    const leftIndex = AGING_RANGE_ORDER.indexOf(left.code as AgingRangeCode);
    const rightIndex = AGING_RANGE_ORDER.indexOf(right.code as AgingRangeCode);
    const leftOrder = left.order ?? (leftIndex === -1 ? 99 : leftIndex);
    const rightOrder = right.order ?? (rightIndex === -1 ? 99 : rightIndex);
    return leftOrder - rightOrder;
  });
}

/** Estima dias médios de atraso a partir das faixas (só títulos em atraso entram no peso). */
export function estimateAverageDaysLateFromAging(
  buckets: ReadonlyArray<{ code: string; count: number }>,
): number | null {
  let lateTitles = 0;
  let weightedDays = 0;

  for (const bucket of buckets) {
    if (bucket.code === "EM_DIA") continue;
    const midpoint = AGING_RANGE_MIDPOINT_DAYS[bucket.code];
    if (midpoint == null || bucket.count <= 0) continue;
    lateTitles += bucket.count;
    weightedDays += bucket.count * midpoint;
  }

  if (lateTitles <= 0) return null;
  return weightedDays / lateTitles;
}
