const UNIT_NAMES: Record<string, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

/** Normalize TOTVS unit codes used by URL/API (never human labels). */
export function normalizeSuppliesUnitCode(code: string | null | undefined): string {
  const trimmed = String(code ?? "").trim();
  if (!trimmed) return "";
  if (trimmed === "01" || trimmed === "02") return trimmed;
  const lower = trimmed.toLowerCase();
  if (lower === "santa catarina") return "01";
  if (lower === "espírito santo" || lower === "espirito santo") return "02";
  return trimmed;
}

/**
 * Human unit name for filters/detail UI.
 * Codes stay in URL, payload and backend only.
 */
export function formatSuppliesUnitName(code: string | null | undefined): string {
  const normalized = normalizeSuppliesUnitCode(code);
  if (!normalized) return "—";
  return UNIT_NAMES[normalized] || `Filial ${normalized}`;
}

/** @deprecated Prefer formatSuppliesUnitName — kept as presentation alias. */
export function formatSuppliesUnitLabel(code: string | null | undefined): string {
  return formatSuppliesUnitName(code);
}

/** Select options from session.allowedUnits only (never invent unauthorized units). */
export function buildSuppliesUnitOptions(allowedUnits: readonly string[]) {
  return allowedUnits
    .map((unit) => normalizeSuppliesUnitCode(unit))
    .filter(Boolean)
    .map((value) => ({
      value,
      label: formatSuppliesUnitName(value),
    }));
}

/**
 * Preferred defaultBranch when allowed; otherwise first allowed unit.
 * Empty allowedUnits → empty string (fail closed — do not invent `01`).
 */
export function resolveDefaultBranch(
  allowedUnits: readonly string[],
  preferred?: string | null,
): string {
  const allowed = allowedUnits.map((unit) => normalizeSuppliesUnitCode(unit)).filter(Boolean);
  const pref = normalizeSuppliesUnitCode(preferred);
  if (pref && allowed.includes(pref)) return pref;
  return allowed[0] ?? "";
}

/** Empty selection means every authorized unit (UI «Todas»). */
export function resolveRequestedBranches(
  selected: readonly string[],
  allowedUnits: readonly string[],
): string[] {
  const allowed = allowedUnits.map((unit) => normalizeSuppliesUnitCode(unit)).filter(Boolean);
  const allowedSet = new Set(allowed);
  const picked = selected
    .map((unit) => normalizeSuppliesUnitCode(unit))
    .filter((code) => allowedSet.has(code));
  if (picked.length === 0) return [...allowed];
  return [...new Set(picked)];
}
