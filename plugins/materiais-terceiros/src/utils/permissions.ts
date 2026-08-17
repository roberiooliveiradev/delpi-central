export const PERM_ACCESS = "materiais-terceiros.access";
export const PERM_VIEW_SC = "materiais-terceiros.view.filial-sc";
export const PERM_VIEW_ES = "materiais-terceiros.view.filial-es";
export const PERM_EXPORT = "materiais-terceiros.export";

export const BRANCH_VIEW_PERMS: Record<string, string> = {
  "01": PERM_VIEW_SC,
  "02": PERM_VIEW_ES,
};

type JwtPayload = {
  permissions?: string[];
  is_superadmin?: boolean;
  isSuperAdmin?: boolean;
  superadmin?: boolean;
  user?: { is_superadmin?: boolean; isSuperAdmin?: boolean };
};

export type PermissionInput = {
  token?: string;
  permissions?: string[] | null;
  hasPermission?: (code: string) => boolean;
  isSuperadmin?: boolean;
};

function decodeJwtPayload(token: string): JwtPayload | null {
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    const normalized = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(
      normalized.length + ((4 - (normalized.length % 4)) % 4),
      "=",
    );
    return JSON.parse(atob(padded)) as JwtPayload;
  } catch {
    return null;
  }
}

function payloadIsSuperadmin(payload: JwtPayload | null): boolean {
  if (!payload) return false;
  return Boolean(
    payload.is_superadmin ||
      payload.isSuperAdmin ||
      payload.superadmin ||
      payload.user?.is_superadmin ||
      payload.user?.isSuperAdmin,
  );
}

export function resolveAuthorizedBranches(input: PermissionInput): string[] {
  if (input.isSuperadmin) return ["01", "02"];

  if (typeof input.hasPermission === "function") {
    const has = input.hasPermission;
    if (has(PERM_ACCESS)) return ["01", "02"];
    return (["01", "02"] as const).filter((branch) => has(BRANCH_VIEW_PERMS[branch]));
  }

  const payload = input.token ? decodeJwtPayload(input.token) : null;
  if (payloadIsSuperadmin(payload)) return ["01", "02"];

  const permissions = new Set([
    ...(input.permissions ?? []),
    ...(payload?.permissions ?? []),
  ]);
  if (permissions.has(PERM_ACCESS)) return ["01", "02"];
  return (["01", "02"] as const).filter((branch) => permissions.has(BRANCH_VIEW_PERMS[branch]));
}

export function canExport(input: PermissionInput): boolean {
  if (input.isSuperadmin) return true;
  if (typeof input.hasPermission === "function") {
    return input.hasPermission(PERM_EXPORT) || input.hasPermission(PERM_ACCESS);
  }
  const payload = input.token ? decodeJwtPayload(input.token) : null;
  if (payloadIsSuperadmin(payload)) return true;
  const permissions = new Set([
    ...(input.permissions ?? []),
    ...(payload?.permissions ?? []),
  ]);
  return permissions.has(PERM_EXPORT) || permissions.has(PERM_ACCESS);
}
