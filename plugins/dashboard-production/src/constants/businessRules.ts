/** Faixa válida alinhada à API (`production_efficiency_valid_range`). */
export const PRODUCTION_EFFICIENCY_VALID_MIN_PCT = 0;
export const PRODUCTION_EFFICIENCY_VALID_MAX_PCT = 199;

export function isProductionEfficiencyOutlier(
  pct: number | null | undefined
): boolean {
  if (pct == null || Number.isNaN(pct)) {
    return true;
  }
  return (
    pct < PRODUCTION_EFFICIENCY_VALID_MIN_PCT ||
    pct > PRODUCTION_EFFICIENCY_VALID_MAX_PCT
  );
}

export function isOeeAppointmentOutlier(
  status: string | null | undefined,
  oeePct: number | null | undefined
): boolean {
  if (status === "outlier") return true;
  if (status === "valid") return false;
  return isProductionEfficiencyOutlier(oeePct);
}
