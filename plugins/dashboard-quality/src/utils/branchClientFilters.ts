import type { MultiSelectOption } from "../components/MultiSelectField";

export function parseDynamicBranchCsv(value: string): string[] {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

export function serializeDynamicBranchCsv(values: string[]): string {
  return values
    .map((value) => value.trim())
    .filter(Boolean)
    .join(",");
}

export function buildBranchOptions(codes: string[]): MultiSelectOption[] {
  return codes.map((code) => ({ value: code, label: `Filial ${code}` }));
}

export function sanitizeBranches(
  values: string[],
  allowed: string[]
): string[] {
  const allowedSet = new Set(allowed);
  return values.filter((value) => allowedSet.has(value));
}

export function resolveApiBranch(branches: string[]): string | undefined {
  return branches.length === 1 ? branches[0] : undefined;
}

export function formatBranchFilterLabel(
  branches: string[],
  emptyLabel = "Todas"
): string {
  if (branches.length === 0) return emptyLabel;
  if (branches.length === 1) return `Filial ${branches[0]}`;
  return `Filiais ${branches.join(", ")}`;
}
