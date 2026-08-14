/** Helpers de comparação de período (YoY / N anos) — espelho tipado do kit. */

/** 0 = sem overlay; 1 = −1a; 2 = −1a e −2a; 3 = até −3a. */
export type CompareYearsCount = 0 | 1 | 2 | 3;

export const MAX_COMPARE_YEARS = 3 as const;

export function clampCompareYears(value: number): CompareYearsCount {
  if (!Number.isFinite(value) || value <= 0) return 0;
  if (value >= 3) return 3;
  return Math.trunc(value) as CompareYearsCount;
}

/** Offsets de ano negativos para overlays (ex.: compareYears=2 → [-1, -2]). */
export function compareYearOffsets(compareYears: CompareYearsCount): number[] {
  const n = clampCompareYears(compareYears);
  if (n === 0) return [];
  return Array.from({ length: n }, (_, index) => -(index + 1));
}
