import { BRANCH_OPTIONS } from "../constants/filterOptions";

function allowedBranches(): Set<string> {
  return new Set(BRANCH_OPTIONS.map((option) => option.value));
}

export function parseBranchCsv(value: string): string[] {
  const allowed = allowedBranches();
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter((entry) => allowed.has(entry));
}

export function serializeBranchCsv(values: string[]): string {
  const allowed = allowedBranches();
  return values
    .map((value) => value.trim())
    .filter((value) => allowed.has(value))
    .join(",");
}

/** Uma filial → parâmetro na API; vazio ou várias → consolidado no servidor. */
export function resolveApiBranch(branches: string[]): string | undefined {
  return branches.length === 1 ? branches[0] : undefined;
}

export function formatBranchFilterLabel(branches: string[]): string {
  if (branches.length === 0 || branches.length >= BRANCH_OPTIONS.length) {
    return "Consolidado";
  }
  if (branches.length === 1) {
    return `Filial ${branches[0]}`;
  }
  return `Filiais ${branches.join(", ")}`;
}
