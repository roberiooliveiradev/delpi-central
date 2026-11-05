import type { PpcBranch } from "../types";

/** Alinhado a production-control.manifest.json e ao BranchAccessService do BFF. */
export const BRANCH_VIEW_PERMISSIONS = {
  "01": "production-control.view.filial-01",
  "02": "production-control.view.filial-02",
} as const satisfies Record<PpcBranch, string>;

export const ALL_PPC_BRANCHES: readonly PpcBranch[] = ["01", "02"];

/**
 * Filiais que o usuário pode ver no Portal PCP.
 * Superadmin vê ambas; demais só as `view.filial-*` efetivas.
 * Lista vazia = fail closed (não inventar 01).
 */
export function resolveAllowedBranches(
  permissions: readonly string[] | undefined,
  isSuperadmin = false,
): PpcBranch[] {
  if (isSuperadmin) return [...ALL_PPC_BRANCHES];
  const set = new Set(permissions ?? []);
  return ALL_PPC_BRANCHES.filter((branch) => set.has(BRANCH_VIEW_PERMISSIONS[branch]));
}

/**
 * Preferência (URL/session) quando autorizada; senão a primeira permitida.
 * Sem filial autorizada → null (não inventar DEFAULT_BRANCH).
 */
export function resolveActiveBranch(
  allowedBranches: readonly PpcBranch[],
  preferred?: string | null,
): PpcBranch | null {
  if (allowedBranches.length === 0) return null;
  if (preferred === "01" || preferred === "02") {
    if (allowedBranches.includes(preferred)) return preferred;
  }
  return allowedBranches[0] ?? null;
}
