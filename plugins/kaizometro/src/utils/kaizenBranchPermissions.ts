import { BRANCHES } from "../constants/kaizen";

/** Códigos RBAC de escopo por unidade (TOTVS 01/02). */
export const KAIZOMETRO_BRANCH_01 = "kaizometro.branch-01";
export const KAIZOMETRO_BRANCH_02 = "kaizometro.branch-02";

const BRANCH_PERM_BY_CODE: Record<string, string> = {
  "01": KAIZOMETRO_BRANCH_01,
  "02": KAIZOMETRO_BRANCH_02,
};

export type BranchOption = { value: string; label: string };

/**
 * Unidades permitidas pelo JWT.
 * Superadmin → ambas. Caso contrário só `kaizometro.branch-*`.
 * `kaizometro.view` sozinho não libera unidades.
 */
export function allowedBranchCodes(
  permissions: string[] | undefined,
  isSuperadmin?: boolean,
): string[] {
  if (isSuperadmin) {
    return BRANCHES.map((b) => b.code);
  }
  const set = new Set(permissions ?? []);
  return BRANCHES.map((b) => b.code).filter((code) => set.has(BRANCH_PERM_BY_CODE[code]));
}

export function branchOptionsForPermissions(
  permissions: string[] | undefined,
  isSuperadmin?: boolean,
): BranchOption[] {
  const allowed = new Set(allowedBranchCodes(permissions, isSuperadmin));
  return BRANCHES.filter((b) => allowed.has(b.code)).map((b) => ({
    value: b.code,
    label: b.label,
  }));
}

export function defaultBranchCode(
  permissions: string[] | undefined,
  isSuperadmin?: boolean,
  preferred?: string,
): string {
  const allowed = allowedBranchCodes(permissions, isSuperadmin);
  if (preferred && allowed.includes(preferred)) return preferred;
  if (allowed.length === 1) return allowed[0];
  return allowed[0] ?? "";
}
