import type { ProductionOeeAppointmentItem } from "../types/production";
import {
  isOeeAppointmentOutlier,
  isProductionEfficiencyLow,
} from "../constants/businessRules";

export type OeeAppointmentStatusKind = "verify" | "low" | "ok";

export function resolveOeeAppointmentStatus(
  row: Pick<ProductionOeeAppointmentItem, "status" | "oee_pct">
): OeeAppointmentStatusKind {
  if (isOeeAppointmentOutlier(row.status, row.oee_pct)) {
    return "verify";
  }
  if (isProductionEfficiencyLow(row.oee_pct)) {
    return "low";
  }
  return "ok";
}

export function formatOeeAppointmentStatusLabel(
  row: Pick<ProductionOeeAppointmentItem, "status" | "oee_pct">
): string {
  const status = resolveOeeAppointmentStatus(row);
  if (status === "verify") return "Verificar";
  if (status === "low") return "Eficiência baixa";
  return "OK";
}
