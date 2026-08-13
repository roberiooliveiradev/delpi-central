import type { RolTargetData } from "../../types/analytics";

/** Gap vs meta SI — max(target − rol, 0); null se sem meta. */
export function resolveGapToTarget(rol: RolTargetData | null | undefined): number | null {
  if (!rol) return null;
  const target = rol.target;
  if (target == null || Number.isNaN(Number(target))) return null;
  const gap = Number(target) - Number(rol.rol ?? 0);
  return gap > 0 ? gap : 0;
}

export function pickPrimaryRolTarget(
  headOffice: RolTargetData | null | undefined,
  branch: RolTargetData | null | undefined,
  activeBranch: string | null | undefined,
): RolTargetData | null {
  if (activeBranch?.trim()) return branch ?? null;
  return headOffice ?? null;
}
