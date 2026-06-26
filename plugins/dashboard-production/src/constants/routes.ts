import { normalizeOperationalUnitCode } from "../utils/operationalUnitLabels";

export const PRODUCTION_BASE_PATH = "/apps/dashboard-production";

export const PRODUCTION_ROUTES = {
  home: PRODUCTION_BASE_PATH,
  oee: `${PRODUCTION_BASE_PATH}/oee`,
  otd: `${PRODUCTION_BASE_PATH}/otd`,
} as const;

export function buildOeeAppointmentPath(
  appointmentId: number | string,
  branch?: string
): string {
  const encoded = encodeURIComponent(String(appointmentId).trim());
  const basePath = `${PRODUCTION_ROUTES.oee}/appointment/${encoded}`;
  const normalizedBranch = normalizeOperationalUnitCode(branch);
  if (!normalizedBranch) return basePath;
  return `${basePath}?branch=${encodeURIComponent(normalizedBranch)}`;
}
