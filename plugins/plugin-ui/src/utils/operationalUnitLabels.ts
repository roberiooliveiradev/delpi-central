import type { MultiSelectOption } from "../components/forms/MultiSelectField";

/** Rótulo do campo de filtro (UI). */
export const OPERATIONAL_UNIT_FIELD_LABEL = "Unidade";

/** Rótulo de coluna em tabelas e detalhes. */
export const OPERATIONAL_UNIT_COLUMN_LABEL = "Unidade";

const UNIT_NAMES: Record<string, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

const UNIT_CODE_BY_LABEL: Record<string, string> = {
  "Santa Catarina": "01",
  "Espírito Santo": "02",
};

export const OPERATIONAL_UNIT_OPTIONS: MultiSelectOption[] = [
  { value: "01", label: "Santa Catarina" },
  { value: "02", label: "Espírito Santo" },
];

/** Código TOTVS (`01`/`02`) para API e URL — aceita rótulo legível por engano. */
export function normalizeOperationalUnitCode(value: string | null | undefined): string {
  const trimmed = (value ?? "").trim();
  if (!trimmed) return "";

  if (trimmed === "01" || trimmed === "02") {
    return trimmed;
  }

  const byExactLabel = UNIT_CODE_BY_LABEL[trimmed];
  if (byExactLabel) {
    return byExactLabel;
  }

  const normalizedLabel = trimmed.toLowerCase();
  for (const [label, code] of Object.entries(UNIT_CODE_BY_LABEL)) {
    if (label.toLowerCase() === normalizedLabel) {
      return code;
    }
  }

  return trimmed;
}

export function formatOperationalUnitCode(code: string | null | undefined, fallback = "—"): string {
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

export function buildOperationalUnitOptions(codes: string[]): MultiSelectOption[] {
  return codes.map((code) => ({
    value: code,
    label: formatOperationalUnitCode(code, code),
  }));
}

export function formatOperationalUnitsFilterLabel(
  branches: string[],
  options?: {
    emptyLabel?: string;
    allSelectedCount?: number;
  },
): string {
  const emptyLabel = options?.emptyLabel ?? "Todas";
  if (branches.length === 0) {
    return emptyLabel;
  }
  if (branches.length === 1) {
    return formatOperationalUnitCode(branches[0], branches[0]);
  }
  if (options?.allSelectedCount != null && branches.length >= options.allSelectedCount) {
    return emptyLabel;
  }
  return branches.map((branch) => formatOperationalUnitCode(branch, branch)).join(", ");
}

export function formatOperationalUnitsPrintLabel(
  branches: string[],
  options?: { allSelectedCount?: number },
): string {
  if (
    branches.length === 0 ||
    (options?.allSelectedCount != null && branches.length >= options.allSelectedCount)
  ) {
    return "Todas";
  }
  if (branches.length === 1) {
    return formatOperationalUnitCode(branches[0], branches[0]);
  }
  return branches
    .map((branch) => formatOperationalUnitCode(branch, branch))
    .join(", ");
}

/** Rótulo de escopo para filtros SI / dashboards (consolidado vs filial). */
export function formatFilterViewScopeLabel(
  viewMode: "consolidated" | "branch",
  branch: string,
): string {
  if (viewMode === "branch" && branch.trim()) {
    return formatOperationalUnitCode(branch.trim(), branch.trim());
  }
  return "Consolidado";
}
