import { hasBranchScopeValues, hasMultiBranchValues } from "./indicatorValueFormatter";

export type IndicatorMetricLayout = "scalar-row" | "branch-grid" | "branch-stack";

type ScopedValues = Record<string, number | null> | null | undefined;

function listBranchKeys(values: ScopedValues): string[] {
  if (!values) return [];

  return Object.keys(values)
    .filter((key) => key.trim() !== "" && key !== "consolidated")
    .sort();
}

function countDistinctBranchKeys(...valueMaps: ScopedValues[]): number {
  const keys = new Set<string>();

  for (const values of valueMaps) {
    for (const key of listBranchKeys(values)) {
      keys.add(key);
    }
  }

  return keys.size;
}

function hasAnyBranchScopedValues(...valueMaps: ScopedValues[]): boolean {
  return valueMaps.some((values) => hasBranchScopeValues(values ?? undefined));
}

/** Define o layout do bloco Meta / Realizado / Nota / Gap conforme o formato dos dados. */
export function resolveIndicatorMetricLayout(
  metrics: {
    goals?: ScopedValues;
    realized?: ScopedValues;
    gaps?: ScopedValues;
  },
  options: { activeBranch?: string } = {},
): IndicatorMetricLayout {
  const activeBranch = (options.activeBranch ?? "").trim();
  if (activeBranch) {
    return "scalar-row";
  }

  const branchCount = countDistinctBranchKeys(
    metrics.goals,
    metrics.realized,
    metrics.gaps,
  );

  if (branchCount >= 3) {
    return "branch-stack";
  }

  if (
    branchCount >= 2 ||
    hasMultiBranchValues(metrics.goals ?? undefined) ||
    hasMultiBranchValues(metrics.realized ?? undefined) ||
    hasMultiBranchValues(metrics.gaps ?? undefined)
  ) {
    return "branch-grid";
  }

  if (hasAnyBranchScopedValues(metrics.goals, metrics.realized, metrics.gaps)) {
    return "branch-grid";
  }

  return "scalar-row";
}

export function resolveIndicatorMetricLayoutClass(
  layout: IndicatorMetricLayout,
): string {
  return `si-indicator-metric-goals--${layout}`;
}
