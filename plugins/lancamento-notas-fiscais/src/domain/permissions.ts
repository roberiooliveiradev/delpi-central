export const LNF_ACCESS = "lancamento-notas-fiscais.access";
export const LNF_CREATE = "lancamento-notas-fiscais.create";
export const LNF_VIEW = "lancamento-notas-fiscais.view";
export const LNF_PROCESS = "lancamento-notas-fiscais.process";
export const LNF_MANAGE = "lancamento-notas-fiscais.manage";

export type LnfPermissionFlags = {
  canAccess: boolean;
  canCreate: boolean;
  canView: boolean;
  canProcess: boolean;
  canManage: boolean;
  canRead: boolean;
};

export function resolveLnfPermissions(
  permissions: string[] | undefined,
  isSuperadmin = false,
): LnfPermissionFlags {
  if (isSuperadmin) {
    return {
      canAccess: true,
      canCreate: true,
      canView: true,
      canProcess: true,
      canManage: true,
      canRead: true,
    };
  }
  const set = new Set(permissions ?? []);
  const canCreate = set.has(LNF_CREATE);
  const canView = set.has(LNF_VIEW);
  const canProcess = set.has(LNF_PROCESS);
  const canManage = set.has(LNF_MANAGE);
  const canAccess = set.has(LNF_ACCESS) || canCreate || canView || canProcess || canManage;
  return {
    canAccess,
    canCreate,
    canView,
    canProcess,
    canManage,
    canRead: canAccess,
  };
}
