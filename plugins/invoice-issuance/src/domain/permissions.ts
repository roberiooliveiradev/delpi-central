export const II_ACCESS = "invoice-issuance.access";
export const II_CREATE = "invoice-issuance.create";
export const II_VIEW = "invoice-issuance.view";
export const II_VIEW_FILIAL_01 = "invoice-issuance.view.filial-01";
export const II_VIEW_FILIAL_02 = "invoice-issuance.view.filial-02";
export const II_PROCESS = "invoice-issuance.process";
export const II_MANAGE = "invoice-issuance.manage";

export type IssuancePermissionFlags = {
  canAccess: boolean;
  canCreate: boolean;
  canView: boolean;
  canProcess: boolean;
  canManage: boolean;
  canRead: boolean;
};

export function resolveIssuancePermissions(
  permissions: string[] | undefined,
  isSuperadmin = false,
): IssuancePermissionFlags {
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
  const canCreate = set.has(II_CREATE);
  const canView = set.has(II_VIEW);
  const canProcess = set.has(II_PROCESS);
  const canManage = set.has(II_MANAGE);
  const hasFilialView =
    set.has(II_VIEW_FILIAL_01) || set.has(II_VIEW_FILIAL_02);
  const canAccess =
    set.has(II_ACCESS) ||
    canCreate ||
    canView ||
    hasFilialView ||
    canProcess ||
    canManage;
  return {
    canAccess,
    canCreate,
    canView,
    canProcess,
    canManage,
    canRead: canAccess,
  };
}
