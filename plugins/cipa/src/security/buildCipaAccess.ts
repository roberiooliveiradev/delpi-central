import type { CipaAccess, CipaUnitCode } from "./cipaAccess";

const UNIT_CODES: CipaUnitCode[] = ["01", "02"];

const VIEW_PERMISSION = "cipa.view";
const MANAGE_PERMISSION = "cipa.manage";
const SIGN_PERMISSION = "cipa.sign";
const ADMIN_PERMISSION = "cipa.admin";

const UNIT_PERMISSIONS: Record<CipaUnitCode, string> = {
  "01": "cipa.unit.filial-01",
  "02": "cipa.unit.filial-02",
};

const UNIT_LABELS: Record<CipaUnitCode, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

const ACTION_PERMISSIONS: Record<string, string> = {
  view: VIEW_PERMISSION,
  view_audit: VIEW_PERMISSION,
  create: MANAGE_PERMISSION,
  edit: MANAGE_PERMISSION,
  delete: MANAGE_PERMISSION,
  submit: MANAGE_PERMISSION,
  cancel: MANAGE_PERMISSION,
  finalize: MANAGE_PERMISSION,
  export: MANAGE_PERMISSION,
  manage_signers: MANAGE_PERMISSION,
  sign: SIGN_PERMISSION,
  admin: ADMIN_PERMISSION,
};

function hasPermission(
  permissions: Set<string>,
  code: string,
  isSuperadmin: boolean,
): boolean {
  if (isSuperadmin) return true;
  return permissions.has(code);
}

function hasGlobalAction(
  permissions: Set<string>,
  action: string,
  isSuperadmin: boolean,
): boolean {
  if (hasPermission(permissions, ADMIN_PERMISSION, isSuperadmin)) return true;
  if (action === "view" || action === "view_audit") {
    return (
      hasPermission(permissions, VIEW_PERMISSION, false) ||
      hasPermission(permissions, MANAGE_PERMISSION, false)
    );
  }
  const actionPermission = ACTION_PERMISSIONS[action];
  if (!actionPermission) return false;
  return hasPermission(permissions, actionPermission, false);
}

function hasUnitAccess(
  permissions: Set<string>,
  unitCode: CipaUnitCode,
  isSuperadmin: boolean,
): boolean {
  if (hasPermission(permissions, ADMIN_PERMISSION, isSuperadmin)) return true;
  return hasPermission(permissions, UNIT_PERMISSIONS[unitCode], false);
}

function hasUnitAction(
  permissions: Set<string>,
  action: string,
  unitCode: CipaUnitCode,
  isSuperadmin: boolean,
): boolean {
  if (hasPermission(permissions, ADMIN_PERMISSION, isSuperadmin)) return true;
  if (!hasUnitAccess(permissions, unitCode, isSuperadmin)) return false;
  return hasGlobalAction(permissions, action, isSuperadmin);
}

function hasUnitReadAccess(
  permissions: Set<string>,
  unitCode: CipaUnitCode,
  isSuperadmin: boolean,
): boolean {
  return (
    hasUnitAction(permissions, "view", unitCode, isSuperadmin) ||
    hasUnitAction(permissions, "create", unitCode, isSuperadmin)
  );
}

/** Espelha `cipa_permissions.build_access_payload` — sem round-trip à API. */
export function buildCipaAccessFromPermissions(
  permissionCodes: string[] | undefined,
  isSuperadmin = false,
): CipaAccess {
  const permissions = new Set(permissionCodes ?? []);
  const isAdmin = hasPermission(permissions, ADMIN_PERMISSION, isSuperadmin);
  const units = UNIT_CODES.flatMap((code) => {
    const view = hasUnitReadAccess(permissions, code, isSuperadmin);
    const manage = hasUnitAction(permissions, "create", code, isSuperadmin);
    const sign = hasUnitAction(permissions, "sign", code, isSuperadmin);
    if (!view && !manage && !sign) return [];
    return [{ id: code, label: UNIT_LABELS[code], view, manage, sign }];
  });

  return {
    admin: isAdmin,
    can_view: isAdmin || hasPermission(permissions, VIEW_PERMISSION, false),
    can_manage: isAdmin || hasPermission(permissions, MANAGE_PERMISSION, false),
    can_sign: isAdmin || hasPermission(permissions, SIGN_PERMISSION, false),
    units,
  };
}
