import type { DemandOrigin, PpcBranch } from "../types";

/** Permissão autoritativa para consultar as necessidades MyWEG no PCP. */
export const MYWEG_NEEDS_VIEW_PERMISSION = "production-control.myweg-needs.view";

/** Na ES, a visão padrão reúne Protheus e MyWEG somente para usuários autorizados. */
export function canViewMywegNeeds(
  permissions: readonly string[] | undefined,
  isSuperadmin = false,
): boolean {
  return isSuperadmin || Boolean(permissions?.includes(MYWEG_NEEDS_VIEW_PERMISSION));
}

export function defaultDemandOrigin(
  branch: PpcBranch,
  canViewMyweg: boolean,
): DemandOrigin {
  return branch === "02" && canViewMyweg ? "both" : "protheus";
}
