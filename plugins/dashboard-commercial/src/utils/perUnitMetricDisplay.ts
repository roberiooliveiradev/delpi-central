const BRANCH_ORDER = ["01", "02"] as const;

export type BranchCode = (typeof BRANCH_ORDER)[number];

export function resolveActiveBranches(
  selectedBranches: string[] = [],
  legacySingleBranch?: string,
): BranchCode[] {
  if (selectedBranches.length === 1) {
    const code = selectedBranches[0];
    if (code === "01" || code === "02") {
      return [code];
    }
  }

  if (selectedBranches.length > 1) {
    return selectedBranches.filter((code): code is BranchCode => code === "01" || code === "02");
  }

  const branch = (legacySingleBranch ?? "").trim();
  if (branch === "01" || branch === "02") {
    return [branch];
  }
  return [...BRANCH_ORDER];
}

/** Realizado ou meta por filial no padrão do painel SI: `01: … | 02: …`. */
export function formatPerUnitBranchMetric(
  values: Partial<Record<BranchCode, number | null | undefined>>,
  formatValue: (value: number) => string,
  activeBranch?: string,
  fallback = "—",
): string {
  const branches = resolveActiveBranches([], activeBranch);
  const parts = branches
    .map((code) => {
      const raw = values[code];
      if (raw == null || Number.isNaN(raw)) {
        return null;
      }
      return `${code}: ${formatValue(raw)}`;
    })
    .filter((part): part is string => part != null);

  if (parts.length >= 2) {
    return parts.join(" | ");
  }
  if (parts.length === 1) {
    return parts[0];
  }
  return fallback;
}
