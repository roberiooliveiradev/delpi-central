import {
  OPERATIONAL_UNIT_FIELD_LABEL,
  OPERATIONAL_UNIT_OPTIONS,
  formatOperationalUnitCode,
  formatOperationalUnitsFilterLabel,
  normalizeOperationalUnitCode,
} from "@delpi/plugin-ui/index";

export {
  OPERATIONAL_UNIT_FIELD_LABEL,
  formatOperationalUnitCode,
  formatOperationalUnitsFilterLabel,
};

/** Field label aligned with commercial analytics chrome. */
export const SUPPLIES_UNIT_FIELD_LABEL = OPERATIONAL_UNIT_FIELD_LABEL;

const CANONICAL_CODES = new Set(
  OPERATIONAL_UNIT_OPTIONS.map((option) => option.value),
);

export function suppliesUnitOptions(allowedUnits: readonly string[]) {
  const allowed = new Set(allowedUnits.map((unit) => normalizeOperationalUnitCode(unit)));
  return OPERATIONAL_UNIT_OPTIONS.filter((option) => allowed.has(option.value)).map(
    (option) => ({ value: option.value, label: option.label }),
  );
}

export function parseSuppliesBranchCsv(value: string): string[] {
  return value
    .split(",")
    .map((entry) => normalizeOperationalUnitCode(entry))
    .filter((entry) => CANONICAL_CODES.has(entry));
}

export function serializeSuppliesBranchCsv(values: readonly string[]): string {
  return values
    .map((value) => normalizeOperationalUnitCode(value))
    .filter((value) => CANONICAL_CODES.has(value))
    .join(",");
}

/** Selected branches sent to the BFF. Empty means Todas (BFF expands to 01+02). */
export function resolveApiBranches(
  branches: readonly string[],
  allowedUnits: readonly string[] = [],
): string[] {
  const allowed = new Set(
    allowedUnits.map((unit) => normalizeOperationalUnitCode(unit)).filter(Boolean),
  );
  const selected: string[] = [];
  for (const value of branches) {
    const code = normalizeOperationalUnitCode(value);
    if (!CANONICAL_CODES.has(code)) continue;
    if (allowed.size > 0 && !allowed.has(code)) continue;
    if (!selected.includes(code)) selected.push(code);
  }
  return selected;
}

/** Series and legacy callers: one unit stays single; zero or many stay consolidated. */
export function resolveApiBranch(
  branches: readonly string[],
  allowedUnits: readonly string[] = [],
): string | undefined {
  const selected = resolveApiBranches(branches, allowedUnits);
  if (selected.length === 1) return selected[0];
  return undefined;
}

/** Units that drive gauges: selection ∩ allowed, or all allowed when empty. */
export function resolveEffectiveUnits(
  branches: readonly string[],
  allowedUnits: readonly string[],
): string[] {
  const allowed = allowedUnits
    .map((unit) => normalizeOperationalUnitCode(unit))
    .filter((unit) => CANONICAL_CODES.has(unit));
  const selected = branches
    .map((value) => normalizeOperationalUnitCode(value))
    .filter((value) => allowed.includes(value));
  return selected.length > 0 ? selected : allowed;
}

export function formatSuppliesScopeBadge(
  branches: readonly string[],
  allowedUnits: readonly string[],
  allLabel: string,
): string {
  const effective = resolveEffectiveUnits(branches, allowedUnits);
  if (effective.length === 0 || effective.length >= allowedUnits.length) {
    return allLabel;
  }
  return (
    formatOperationalUnitsFilterLabel(effective, {
      allSelectedCount: Math.max(allowedUnits.length, OPERATIONAL_UNIT_OPTIONS.length),
    }) ?? formatOperationalUnitCode(effective[0], effective[0])
  );
}
