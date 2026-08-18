import type { RolTargetData } from "../../types/analytics";

function periodGoal(rol: RolTargetData | null | undefined): number | null {
  if (!rol) return null;
  const raw = rol.comparable_goal ?? rol.target;
  if (raw == null || Number.isNaN(Number(raw))) return null;
  const value = Number(raw);
  if (value <= 0) return null;
  return value;
}

/** Gap vs meta SI — max(meta do período − rol, 0); null se sem meta. */
export function resolveGapToTarget(rol: RolTargetData | null | undefined): number | null {
  const target = periodGoal(rol);
  if (target == null) return null;
  const gap = target - Number(rol?.rol ?? 0);
  return gap > 0 ? gap : 0;
}

/**
 * Mesma fonte do card ROL: 01 = matriz (head office), 02 = ES.
 * Sem unidade: consolidado no caller (`resolveOverviewGapToTarget`).
 */
export function pickPrimaryRolTarget(
  headOffice: RolTargetData | null | undefined,
  branch: RolTargetData | null | undefined,
  activeBranch: string | null | undefined,
): RolTargetData | null {
  const code = (activeBranch ?? "").trim();
  if (code === "01") return headOffice ?? null;
  if (code === "02") return branch ?? null;
  return null;
}

/** Gap alinhado ao ROL exibido (unidade filtrada ou soma das unidades com meta). */
export function resolveOverviewGapToTarget(
  headOffice: RolTargetData | null | undefined,
  branch: RolTargetData | null | undefined,
  activeBranch: string | null | undefined,
): number | null {
  const code = (activeBranch ?? "").trim();
  if (code === "01" || code === "02") {
    return resolveGapToTarget(pickPrimaryRolTarget(headOffice, branch, code));
  }

  let metaSum = 0;
  let rolSum = 0;
  let hasMeta = false;
  for (const slice of [headOffice, branch]) {
    const meta = periodGoal(slice);
    if (meta == null) continue;
    hasMeta = true;
    metaSum += meta;
    rolSum += Number(slice?.rol ?? 0);
  }
  if (!hasMeta) return null;
  const gap = metaSum - rolSum;
  return gap > 0 ? gap : 0;
}
