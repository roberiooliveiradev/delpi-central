import type { MeProfile } from "../api/meApi";
import { AUDITORIA_5S_ADMIN_BY_BRANCH } from "../constants/permissions";

function profilePermissions(profile: MeProfile | null | undefined): Set<string> {
  return new Set(profile?.permissions ?? []);
}

function isSuperadmin(profile: MeProfile | null | undefined): boolean {
  return Boolean(profile?.is_superadmin);
}

/** Admin da filial atual — necessário para encerrar NCs sem tratar. */
export function hasAdminPermission(
  profile: MeProfile | null | undefined,
  branch: "01" | "02" | string | null | undefined,
): boolean {
  if (!profile) return false;
  if (isSuperadmin(profile)) return true;
  if (branch !== "01" && branch !== "02") return false;
  return profilePermissions(profile).has(AUDITORIA_5S_ADMIN_BY_BRANCH[branch]);
}
