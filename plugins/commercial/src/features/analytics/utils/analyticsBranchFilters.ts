import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  OPERATIONAL_UNIT_FIELD_LABEL,
  OPERATIONAL_UNIT_OPTIONS,
  formatOperationalUnitCode,
  formatOperationalUnitsFilterLabel,
  normalizeOperationalUnitCode,
} from "@delpi/plugin-ui/index";

export {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  OPERATIONAL_UNIT_FIELD_LABEL,
  formatOperationalUnitCode,
};

/** Campo do filtro analytics — alinhado ao dashboard-commercial. */
export const ANALYTICS_UNIT_FIELD_LABEL = "Unidade (indicadores)";

export const ANALYTICS_BRANCH_OPTIONS = OPERATIONAL_UNIT_OPTIONS.map((option) => ({
  value: option.value,
  label: option.label,
}));

/** Séries ROL: códigos API `rol_matrix`/`rol_branch` ↔ unidades 01/02. */
export const ANALYTICS_ROL_SERIES_LABELS = {
  unit01: `ROL ${formatOperationalUnitCode("01")}`,
  unit02: `ROL ${formatOperationalUnitCode("02")}`,
} as const;

export const ANALYTICS_OTD_SERIES_LABELS = {
  unit01: `OTD ${formatOperationalUnitCode("01")}`,
  unit02: `OTD ${formatOperationalUnitCode("02")}`,
} as const;

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
