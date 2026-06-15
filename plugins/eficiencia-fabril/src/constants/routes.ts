import type { BranchRouteCode } from "./branches";

export const EFICIENCIA_FABRIL_BASE_PATH = "/apps/eficiencia-fabril";

export function buildEficienciaFabrilDashboardPath(branchRoute: BranchRouteCode): string {
  return `${EFICIENCIA_FABRIL_BASE_PATH}/${branchRoute.toLowerCase()}`;
}

export function buildEficienciaFabrilAppointmentPath(
  branchRoute: BranchRouteCode,
  appointmentId: number | string,
  branch?: string
): string {
  const encoded = encodeURIComponent(String(appointmentId).trim());
  const basePath = `${buildEficienciaFabrilDashboardPath(branchRoute)}/appointment/${encoded}`;
  if (!branch) return basePath;
  return `${basePath}?branch=${encodeURIComponent(branch)}`;
}
