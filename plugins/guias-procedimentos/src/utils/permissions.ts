import type { MeProfile } from "../api/meApi";

export const GUIAS_MANAGE_PERMISSION = "guias-procedimentos.manage";
export const GUIAS_ACCESS_PERMISSION = "guias-procedimentos.access";

export function hasManagePermission(profile: MeProfile | null | undefined): boolean {
  if (!profile) return false;
  if (profile.is_superadmin) return true;
  return (profile.permissions ?? []).includes(GUIAS_MANAGE_PERMISSION);
}
