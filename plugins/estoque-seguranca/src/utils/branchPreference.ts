import type { SafetyStockFiltersData } from "../types/safetyStock";

export const SAFETY_STOCK_BRANCH_STORAGE_KEY = "estoque-seguranca:preferred-branch:v1";

/** Preferência simples por navegador; não substitui as filiais autorizadas da API. */
export function readPreferredSafetyStockBranch(): string {
  try {
    if (typeof window === "undefined") return "";
    const stored = window.localStorage.getItem(SAFETY_STOCK_BRANCH_STORAGE_KEY);
    return stored === "01" || stored === "02" ? stored : "";
  } catch {
    return "";
  }
}

export function savePreferredSafetyStockBranch(branch: string): void {
  if (branch !== "01" && branch !== "02") return;
  try {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(SAFETY_STOCK_BRANCH_STORAGE_KEY, branch);
    }
  } catch {
    // Ambientes sem storage continuam funcionando com o estado em memória.
  }
}

/** Nunca devolve uma filial fora da lista autorizada; só resolve após bootstrap. */
export function resolveAuthorizedSafetyStockBranch(
  selectedBranch: string,
  options: SafetyStockFiltersData | null,
  preferredBranch: string,
): string {
  const authorized = options?.authorized_branches ?? [];
  if (selectedBranch && authorized.includes(selectedBranch)) return selectedBranch;
  if (!selectedBranch && preferredBranch && authorized.includes(preferredBranch)) {
    return preferredBranch;
  }
  if (options?.branch && authorized.includes(options.branch)) return options.branch;
  return authorized[0] ?? "";
}
