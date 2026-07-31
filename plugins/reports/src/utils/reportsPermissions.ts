/** Códigos alinhados a `reports.manifest.json` e `api_delpi_permissions.py`. */

export const REPORTS_VIEW = "reports.view";
export const REPORTS_MANAGE = "reports.manage";
export const REPORTS_NOTES_MANAGE = "reports.notes.manage";
export const REPORTS_VIEW_FILIAL_SC = "reports.view.filial-sc";
export const REPORTS_VIEW_FILIAL_ES = "reports.view.filial-es";
export const REPORTS_MANAGE_FILIAL_SC = "reports.manage.filial-sc";
export const REPORTS_MANAGE_FILIAL_ES = "reports.manage.filial-es";

export type ReportsPermissionFlags = {
  /** Visão geral / Relatórios (cadastro, agenda, envio). */
  canUseAdminNav: boolean;
  /** Aba e rotas de acompanhamentos. */
  canUseFollowUpNav: boolean;
};

export type ReportsPermissionInput = {
  permissions?: string[] | null;
  isSuperadmin?: boolean;
  hasPermission?: (code: string) => boolean;
};

function granted(args: ReportsPermissionInput): (code: string) => boolean {
  if (typeof args.hasPermission === "function") {
    return args.hasPermission;
  }
  const set = new Set(args.permissions ?? []);
  return (code: string) => set.has(code);
}

/**
 * Admin UI do plugin: manifesto `/apps/reports` exige `reports.view`.
 * Filial sozinha (view.filial-*) NÃO abre Visão geral/Relatórios — só escopo de dados.
 */
export function resolveReportsPermissions(
  args: ReportsPermissionInput,
): ReportsPermissionFlags {
  if (args.isSuperadmin) {
    return { canUseAdminNav: true, canUseFollowUpNav: true };
  }

  const has = granted(args);
  const canManage =
    has(REPORTS_MANAGE) ||
    has(REPORTS_MANAGE_FILIAL_SC) ||
    has(REPORTS_MANAGE_FILIAL_ES);
  const canUseAdminNav = has(REPORTS_VIEW) || canManage;
  // Operacional (só notes.manage) vê só Acompanhamentos; view/manage também veem a aba.
  const canUseFollowUpNav =
    has(REPORTS_NOTES_MANAGE) || canUseAdminNav;

  return { canUseAdminNav, canUseFollowUpNav };
}
