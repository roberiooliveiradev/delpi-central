/** Rótulo do campo de filtro (UI). */
export const OPERATIONAL_UNIT_FIELD_LABEL = "Unidade";

/** Rótulo de coluna em tabelas e detalhes. */
export const OPERATIONAL_UNIT_COLUMN_LABEL = "Unidade";

const UNIT_NAMES: Record<string, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

export const OPERATIONAL_UNIT_OPTIONS = [
  { value: "01", label: "Santa Catarina" },
  { value: "02", label: "Espírito Santo" },
] as const;

export function formatOperationalUnitCode(
  code: string | null | undefined,
  fallback = "—",
): string {
  const trimmed = (code ?? "").trim();
  if (!trimmed) return fallback;
  return UNIT_NAMES[trimmed] ?? trimmed;
}

export function formatGoalScopeUnitLabel(
  goalScopeBranch?: string | null,
  scopeType?: string | null,
): string {
  const branch = (goalScopeBranch ?? "").trim();
  if (branch === "01" || branch === "02") {
    return `Meta ${formatOperationalUnitCode(branch, branch)}`;
  }
  if (branch) {
    return `Meta ${formatOperationalUnitCode(branch, branch)}`;
  }
  if ((scopeType ?? "").trim() === "per_unit") {
    return "Meta por unidade";
  }
  return "Meta consolidada";
}

export function formatFilterViewScopeLabel(
  viewMode: "consolidated" | "branch",
  branch: string,
): string {
  if (viewMode === "branch" && branch.trim()) {
    return formatOperationalUnitCode(branch.trim(), branch.trim());
  }
  return "Consolidado";
}
