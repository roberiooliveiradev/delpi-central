export function canUseDelpiMes(
  permissions: ReadonlySet<string>,
  permission: string,
  isSuperadmin: boolean,
): boolean {
  return isSuperadmin || permissions.has(permission);
}

export function hasDelpiMesProductAccess(
  permissions: ReadonlySet<string>,
  isSuperadmin: boolean,
): boolean {
  return canUseDelpiMes(permissions, "delpi-mes.access", isSuperadmin);
}
