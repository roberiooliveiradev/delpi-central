export const PP_ACCESS = "production-pulse.access";
export const PP_DEVICES_VIEW = "production-pulse.devices.view";
export const PP_DEVICES_MANAGE = "production-pulse.devices.manage";
export const PP_DEVICES_COMMAND = "production-pulse.devices.command";
export const PP_OPERATOR = "production-pulse.operator";
export const PP_VIEW_FILIAL_01 = "production-pulse.view.filial-01";
export const PP_VIEW_FILIAL_02 = "production-pulse.view.filial-02";
export const PP_ADMIN = "production-pulse.admin";

export type ProductionPulsePermissionFlags = {
  canAccess: boolean;
  canViewDevices: boolean;
  canManageDevices: boolean;
  canCommandDevices: boolean;
  canOperator: boolean;
  isAdmin: boolean;
  allowedBranches: string[];
};

const BRANCH_PERMISSIONS: Array<{ branch: string; permission: string }> = [
  { branch: "01", permission: PP_VIEW_FILIAL_01 },
  { branch: "02", permission: PP_VIEW_FILIAL_02 },
];

export function resolveProductionPulsePermissions(
  permissions: string[] | undefined,
  isSuperadmin = false,
): ProductionPulsePermissionFlags {
  if (isSuperadmin) {
    return {
      canAccess: true,
      canViewDevices: true,
      canManageDevices: true,
      canCommandDevices: true,
      canOperator: true,
      isAdmin: true,
      allowedBranches: ["01", "02"],
    };
  }

  const set = new Set(permissions ?? []);
  const isAdmin = set.has(PP_ADMIN);
  const canViewDevices = isAdmin || set.has(PP_DEVICES_VIEW);
  const canManageDevices = isAdmin || set.has(PP_DEVICES_MANAGE);
  const canCommandDevices = isAdmin || set.has(PP_DEVICES_COMMAND) || canManageDevices;
  const canOperator = isAdmin || set.has(PP_OPERATOR);
  const hasFilialView = BRANCH_PERMISSIONS.some(({ permission }) => set.has(permission));
  const canAccess =
    isAdmin ||
    set.has(PP_ACCESS) ||
    canViewDevices ||
    canManageDevices ||
    canCommandDevices ||
    canOperator ||
    hasFilialView;

  const allowedBranches = isAdmin
    ? ["01", "02"]
    : BRANCH_PERMISSIONS.filter(({ permission }) => set.has(permission)).map(({ branch }) => branch);

  return {
    canAccess,
    canViewDevices,
    canManageDevices,
    canCommandDevices,
    canOperator,
    isAdmin,
    allowedBranches,
  };
}
