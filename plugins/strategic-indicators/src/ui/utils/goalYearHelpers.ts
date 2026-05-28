const MIN_GOAL_YEAR = 2020;
const MAX_GOAL_YEAR = 2100;

export function clampGoalYear(year: number): number {
  if (!Number.isFinite(year)) {
    return new Date().getFullYear();
  }
  return Math.min(MAX_GOAL_YEAR, Math.max(MIN_GOAL_YEAR, Math.round(year)));
}

export function sortYearsDesc(years: number[]): number[] {
  return [...new Set(years.filter((year) => Number.isFinite(year)))].sort(
    (left, right) => right - left,
  );
}

/** Ano imediatamente anterior ao maior ciclo existente (ex.: só 2026 → sugere 2025). */
export function suggestYearBeforeLatest(existingYears: number[]): number | null {
  const sortedAsc = [...new Set(existingYears)].sort((a, b) => a - b);
  if (!sortedAsc.length) return null;

  const maxYear = sortedAsc[sortedAsc.length - 1];
  for (let year = maxYear - 1; year >= maxYear - 10; year -= 1) {
    if (!sortedAsc.includes(year)) {
      return clampGoalYear(year);
    }
  }

  return clampGoalYear(maxYear + 1);
}

/** Origem natural para copiar metas para `targetYear` (ex.: destino 2025 → origem 2026). */
export function pickSourceYearForTarget(
  existingYears: number[],
  targetYear: number,
): number {
  const sortedDesc = sortYearsDesc(existingYears);
  if (!sortedDesc.length) {
    return clampGoalYear(targetYear - 1);
  }

  const newer = sortedDesc.find((year) => year > targetYear);
  if (typeof newer === "number") {
    return newer;
  }

  const older = sortedDesc.find((year) => year < targetYear);
  if (typeof older === "number") {
    return older;
  }

  return sortedDesc[0];
}

export function buildYearSelectOptions(
  existingYears: number[],
  extraYears: number[] = [],
): number[] {
  const finiteExtra = extraYears.filter((year) => Number.isFinite(year));
  const merged = sortYearsDesc([...existingYears, ...finiteExtra]);
  const options = new Set<number>(merged);

  if (finiteExtra.length > 0) {
    const minExtra = Math.min(...finiteExtra);
    const maxExtra = Math.max(...finiteExtra);
    for (let year = minExtra; year <= maxExtra + 2; year += 1) {
      if (year >= MIN_GOAL_YEAR && year <= MAX_GOAL_YEAR) {
        options.add(year);
      }
    }
  }

  return sortYearsDesc([...options]);
}

export { MIN_GOAL_YEAR, MAX_GOAL_YEAR };
