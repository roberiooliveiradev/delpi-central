import {
  OPERATIONAL_UNIT_OPTIONS,
  formatOperationalUnitsFilterLabel,
  normalizeOperationalUnitCode,
} from "@delpi/plugin-ui/index";

export const ANALYTICS_BRANCH_OPTIONS = OPERATIONAL_UNIT_OPTIONS.map((option) => ({
  value: option.value,
  label: option.label,
}));

export function parseAnalyticsBranchCsv(value: string): string[] {
  const allowed = new Set(ANALYTICS_BRANCH_OPTIONS.map((option) => option.value));
  return value
    .split(",")
    .map((entry) => normalizeOperationalUnitCode(entry))
    .filter((entry) => allowed.has(entry));
}

export function serializeAnalyticsBranchCsv(values: string[]): string {
  const allowed = new Set(ANALYTICS_BRANCH_OPTIONS.map((option) => option.value));
  return values
    .map((value) => value.trim())
    .filter((value) => allowed.has(value))
    .join(",");
}

export function resolveAnalyticsApiBranch(branches: string[]): string | undefined {
  return branches.length === 1 ? branches[0] : undefined;
}

export function formatAnalyticsBranchFilterLabel(branches: string[]): string | null {
  if (branches.length === 0) return null;
  if (branches.length >= ANALYTICS_BRANCH_OPTIONS.length) return null;
  return formatOperationalUnitsFilterLabel(branches, {
    allSelectedCount: ANALYTICS_BRANCH_OPTIONS.length,
  });
}
