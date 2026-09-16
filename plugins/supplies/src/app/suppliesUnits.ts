const UNIT_NAMES: Record<string, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

/** Normalize TOTVS unit codes used by URL/API (never human labels). */
function normalizeUnitCode(code: string | null | undefined): string {
  const trimmed = (code ?? "").trim();
  if (!trimmed) return "";
  if (trimmed === "01" || trimmed === "02") return trimmed;
  const lower = trimmed.toLowerCase();
  if (lower === "santa catarina") return "01";
  if (lower === "espírito santo" || lower === "espirito santo") return "02";
  return trimmed;
}

/**
 * Human-readable unit label for filters/detail UI.
 * API/URL continue to use the TOTVS code (`01` / `02`).
 */
export function formatSuppliesUnitLabel(code: string | null | undefined): string {
  const normalized = normalizeUnitCode(code);
  if (!normalized) return "—";
  const name = UNIT_NAMES[normalized];
  if (!name) return `Filial ${normalized}`;
  return `${name} (${normalized})`;
}

/** Select options from session.allowedUnits only (never invent unauthorized units). */
export function buildSuppliesUnitOptions(allowedUnits: readonly string[]) {
  return allowedUnits
    .map((unit) => normalizeUnitCode(unit))
    .filter(Boolean)
    .map((value) => ({
      value,
      label: formatSuppliesUnitLabel(value),
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
  const allowed = allowedUnits.map((unit) => normalizeUnitCode(unit)).filter(Boolean);
  const pref = normalizeUnitCode(preferred);
  if (pref && allowed.includes(pref)) return pref;
  return allowed[0] ?? "";
}
