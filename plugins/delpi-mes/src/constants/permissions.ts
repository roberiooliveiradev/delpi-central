export const DELPI_MES_DOWNTIME_REASONS_MANAGE = "delpi-mes.downtime-reasons.manage";
export const DELPI_MES_DOWNTIMES_CLASSIFY = "delpi-mes.downtimes.classify";
export const DELPI_MES_DOWNTIMES_TREAT = "delpi-mes.downtimes.treat";

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
