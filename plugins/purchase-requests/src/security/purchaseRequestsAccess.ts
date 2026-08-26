export const ACCESS_PERMISSION = "purchase-requests.access";
export const ADMIN_PERMISSION = "purchase-requests.admin";
export const RBAC_MANAGE_PERMISSION = "rbac.manage";
export const VIEW_ALL_PERMISSION = "purchase-requests.view-all";
export const EXPORT_PERMISSION = "purchase-requests.export";

export const UNIT_PERMISSIONS: Record<"01" | "02", string> = {
  "01": "purchase-requests.unit.filial-01",
  "02": "purchase-requests.unit.filial-02",
};

export type BranchOption = {
  value: "01" | "02";
  label: string;
};

export type PurchaseRequestsAccess = {
  canView: boolean;
  canAdmin: boolean;
  canViewAll: boolean;
  canExport: boolean;
  branches: BranchOption[];
  defaultBranch: "01" | "02" | "";
};

function hasPermission(codes: string[], code: string): boolean {
  return codes.includes(code);
}

export function buildAccessFromPermissions(
  permissions: string[] | undefined,
  isSuperadmin: boolean,
): PurchaseRequestsAccess {
  const codes = permissions ?? [];
  const canAdmin =
    isSuperadmin ||
    hasPermission(codes, ADMIN_PERMISSION) ||
    hasPermission(codes, RBAC_MANAGE_PERMISSION);
  const canView =
    isSuperadmin || canAdmin || hasPermission(codes, ACCESS_PERMISSION);
  const canViewAll =
    isSuperadmin || hasPermission(codes, VIEW_ALL_PERMISSION) || canAdmin;
  const canExport =
    isSuperadmin || hasPermission(codes, EXPORT_PERMISSION) || canAdmin;

  const branches: BranchOption[] = [];
  if (isSuperadmin || canAdmin || hasPermission(codes, UNIT_PERMISSIONS["01"])) {
    branches.push({ value: "01", label: "Filial 01 (SC)" });
  }
  if (isSuperadmin || canAdmin || hasPermission(codes, UNIT_PERMISSIONS["02"])) {
    branches.push({ value: "02", label: "Filial 02 (ES)" });
  }

  return {
    canView,
    canAdmin,
    canViewAll,
    canExport,
    branches,
    defaultBranch: branches[0]?.value ?? "",
  };
}

export function canAccessBranch(access: PurchaseRequestsAccess, branch: string): boolean {
  return access.branches.some((item) => item.value === branch);
}
