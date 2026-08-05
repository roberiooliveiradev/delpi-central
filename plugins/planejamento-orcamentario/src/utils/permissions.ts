import type { MeProfile } from "../api/meApi";

export const PERM_ACCESS = "planejamento-orcamentario.access";
export const PERM_GUIDANCE_VIEW = "planejamento-orcamentario.guidance.view";
export const PERM_GUIDANCE_MANAGE = "planejamento-orcamentario.guidance.manage";
export const PERM_SCOPES_MANAGE = "planejamento-orcamentario.scopes.manage";
export const PERM_ADMIN = "planejamento-orcamentario.admin";
export const PERM_CAPEX_SUBMIT = "planejamento-orcamentario.capex.submit";
export const PERM_CAPEX_APPROVE = "planejamento-orcamentario.capex.approve";
export const PERM_CAPEX_CONSOLIDATION_VIEW =
  "planejamento-orcamentario.capex.consolidation.view";
export const PERM_CAPEX_EXPORT = "planejamento-orcamentario.capex.export";
export const PERM_PERSONNEL_VIEW = "planejamento-orcamentario.personnel.view";
export const PERM_PERSONNEL_EDIT = "planejamento-orcamentario.personnel.edit";
export const PERM_PERSONNEL_SUBMIT = "planejamento-orcamentario.personnel.submit";
export const PERM_PERSONNEL_APPROVE = "planejamento-orcamentario.personnel.approve";

export function hasPermission(profile: MeProfile | null, code: string): boolean {
  if (!profile?.permissions?.length) return false;
  return profile.permissions.includes(code);
}

export function hasAdminAccess(profile: MeProfile | null): boolean {
  return hasPermission(profile, PERM_ADMIN);
}

export function hasGuidanceManageAccess(profile: MeProfile | null): boolean {
  return (
    hasPermission(profile, PERM_GUIDANCE_MANAGE) || hasPermission(profile, PERM_ADMIN)
  );
}

export function hasScopesManageAccess(profile: MeProfile | null): boolean {
  return (
    hasPermission(profile, PERM_SCOPES_MANAGE) || hasPermission(profile, PERM_ADMIN)
  );
}

export function hasCapexSubmitAccess(profile: MeProfile | null): boolean {
  return (
    hasPermission(profile, PERM_CAPEX_SUBMIT) || hasPermission(profile, PERM_ADMIN)
  );
}

export function hasCapexApproveAccess(profile: MeProfile | null): boolean {
  return (
    hasPermission(profile, PERM_CAPEX_APPROVE) || hasPermission(profile, PERM_ADMIN)
  );
}

export function hasCapexConsolidationViewAccess(profile: MeProfile | null): boolean {
  return (
    hasPermission(profile, PERM_CAPEX_CONSOLIDATION_VIEW) ||
    hasPermission(profile, PERM_ADMIN)
  );
}

export function hasCapexExportAccess(profile: MeProfile | null): boolean {
  return (
    hasPermission(profile, PERM_CAPEX_EXPORT) || hasPermission(profile, PERM_ADMIN)
  );
}

export function hasPersonnelViewAccess(profile: MeProfile | null): boolean {
  return (
    hasPermission(profile, PERM_PERSONNEL_VIEW) ||
    hasPermission(profile, PERM_PERSONNEL_EDIT) ||
    hasPermission(profile, PERM_ADMIN)
  );
}

export function hasPersonnelEditAccess(profile: MeProfile | null): boolean {
  return (
    hasPermission(profile, PERM_PERSONNEL_EDIT) || hasPermission(profile, PERM_ADMIN)
  );
}

export function hasPersonnelSubmitAccess(profile: MeProfile | null): boolean {
  return (
    hasPermission(profile, PERM_PERSONNEL_SUBMIT) || hasPermission(profile, PERM_ADMIN)
  );
}

export function hasPersonnelApproveAccess(profile: MeProfile | null): boolean {
  return (
    hasPermission(profile, PERM_PERSONNEL_APPROVE) || hasPermission(profile, PERM_ADMIN)
  );
}
