import { COMMERCIAL_BRANCH_OPTIONS } from "../constants/filterOptions";

export function parseCommercialBranchCsv(value: string): string[] {
  const allowed = new Set(COMMERCIAL_BRANCH_OPTIONS.map((option) => option.value));

  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter((entry) => allowed.has(entry));
}

export function serializeCommercialBranchCsv(values: string[]): string {
  const allowed = new Set(COMMERCIAL_BRANCH_OPTIONS.map((option) => option.value));

  return values
    .map((value) => value.trim())
    .filter((value) => allowed.has(value))
    .join(",");
}

/** Uma filial → parâmetro `branch` na API; vazio ou várias → consolidado no servidor. */
export function resolveCommercialApiBranch(branches: string[]): string | undefined {
  return branches.length === 1 ? branches[0] : undefined;
}

/** Rótulo de escopo para KPIs (null = usar texto consolidado padrão). */
export function formatCommercialBranchFilterLabel(branches: string[]): string | null {
  if (branches.length === 0) {
    return null;
  }
  if (branches.length === 1) {
    return `Filial ${branches[0]}`;
  }
  if (branches.length >= COMMERCIAL_BRANCH_OPTIONS.length) {
    return null;
  }
  return `Filiais ${branches.join(", ")}`;
}

/** Texto para impressão / resumo do relatório. */
export function formatCommercialBranchPrintLabel(branches: string[]): string {
  if (branches.length === 0 || branches.length >= COMMERCIAL_BRANCH_OPTIONS.length) {
    return "Todas";
  }
  if (branches.length === 1) {
    return branches[0];
  }
  return branches.join(", ");
}
