import {
  OPERATIONAL_UNIT_OPTIONS,
  formatOperationalUnitsFilterLabel,
  normalizeOperationalUnitCode,
} from "@delpi/plugin-ui/index";

export const GESTAO_BRANCH_OPTIONS = OPERATIONAL_UNIT_OPTIONS.map((option) => ({
  value: option.value,
  label: option.label,
}));

export function parseGestaoBranchCsv(value: string): string[] {
  const allowed = new Set(GESTAO_BRANCH_OPTIONS.map((option) => option.value));
  return value
    .split(",")
    .map((entry) => normalizeOperationalUnitCode(entry))
    .filter((entry) => allowed.has(entry));
}

export function serializeGestaoBranchCsv(values: string[]): string {
  const allowed = new Set(GESTAO_BRANCH_OPTIONS.map((option) => option.value));
  return values
    .map((value) => value.trim())
    .filter((value) => allowed.has(value))
    .join(",");
}

export function resolveGestaoApiBranch(branches: string[]): string | undefined {
  return branches.length === 1 ? branches[0] : undefined;
}

export function formatGestaoBranchFilterLabel(branches: string[]): string | null {
  if (branches.length === 0) return null;
  if (branches.length >= GESTAO_BRANCH_OPTIONS.length) return null;
  return formatOperationalUnitsFilterLabel(branches, {
    allSelectedCount: GESTAO_BRANCH_OPTIONS.length,
  });
}
