/** Labels / helpers for multi-year YoY overlay checkboxes (0–3). */

export type CompareYearsCount = 0 | 1 | 2 | 3;

export const MAX_COMPARE_YEARS = 3 as const;

export function clampCompareYears(value: number): CompareYearsCount {
  if (!Number.isFinite(value)) return 0;
  const n = Math.trunc(value);
  if (n <= 0) return 0;
  if (n === 1) return 1;
  if (n === 2) return 2;
  return 3;
}

export function compareYearOffsets(compareYears: CompareYearsCount): number[] {
  const n = clampCompareYears(compareYears);
  return Array.from({ length: n }, (_, index) => -(index + 1));
}

export type CompareYearsOverlayLabels = {
  priorYear: string;
  plus2: string;
  plus3: string;
  priorYearSummary?: string;
  plus2Summary?: string;
  plus3Summary?: string;
  priorYearHint?: string;
  plus2Hint?: string;
  plus3Hint?: string;
};

/**
 * Cascading YoY checkboxes: −1 enables −2; −2 enables −3.
 * Returns option descriptors for ChartOverlayOptionsPopover.
 */
export function buildCompareYearsOverlayOptions(args: {
  compareYears: CompareYearsCount;
  onCompareYearsChange: (value: CompareYearsCount) => void;
  labels: CompareYearsOverlayLabels;
  disabled?: boolean;
}): Array<{
  id: string;
  label: string;
  summaryLabel: string;
  checked: boolean;
  disabled: boolean;
  hint?: string;
  hintAriaLabel?: string;
  onChange: (checked: boolean) => void;
}> {
  const { compareYears, onCompareYearsChange, labels, disabled = false } = args;
  const yoyActive = compareYears >= 1;
  const compare2 = compareYears >= 2;
  const compare3 = compareYears >= 3;

  return [
    {
      id: "yoy-1",
      label: labels.priorYear,
      summaryLabel: labels.priorYearSummary ?? labels.priorYear,
      checked: yoyActive,
      disabled,
      hint: labels.priorYearHint,
      hintAriaLabel: labels.priorYearHint ? "Ajuda: comparar ano anterior" : undefined,
      onChange: (checked: boolean) =>
        onCompareYearsChange(checked ? clampCompareYears(Math.max(compareYears, 1)) : 0),
    },
    {
      id: "yoy-2",
      label: labels.plus2,
      summaryLabel: labels.plus2Summary ?? labels.plus2,
      checked: compare2,
      disabled: disabled || !yoyActive,
      hint: labels.plus2Hint,
      hintAriaLabel: labels.plus2Hint ? "Ajuda: +2 anos" : undefined,
      onChange: (checked: boolean) =>
        onCompareYearsChange(
          checked ? clampCompareYears(Math.max(compareYears, 2)) : yoyActive ? 1 : 0,
        ),
    },
    {
      id: "yoy-3",
      label: labels.plus3,
      summaryLabel: labels.plus3Summary ?? labels.plus3,
      checked: compare3,
      disabled: disabled || compareYears < 2,
      hint: labels.plus3Hint,
      hintAriaLabel: labels.plus3Hint ? "Ajuda: +3 anos" : undefined,
      onChange: (checked: boolean) =>
        onCompareYearsChange(checked ? 3 : compare2 ? 2 : yoyActive ? 1 : 0),
    },
  ];
}
