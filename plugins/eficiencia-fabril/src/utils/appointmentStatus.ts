import {
  isProductionEfficiencyLow,
  isProductionEfficiencyOutlier,
} from "../constants/businessRules";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";

export type EficienciaFabrilAppointmentStatusKind = "verify" | "low" | "ok";

export function resolveEficienciaFabrilAppointmentStatus(
  item: Pick<EficienciaFabrilItem, "eficiencia_percentual" | "status_registro">
): EficienciaFabrilAppointmentStatusKind {
  if (isProductionEfficiencyOutlier(item.eficiencia_percentual)) {
    return "verify";
  }
  if (isProductionEfficiencyLow(item.eficiencia_percentual)) {
    return "low";
  }
  return "ok";
}

export function formatEficienciaFabrilAppointmentStatusLabel(
  item: Pick<EficienciaFabrilItem, "eficiencia_percentual" | "status_registro">
): string {
  const status = resolveEficienciaFabrilAppointmentStatus(item);
  if (status === "verify") return "Verificar";
  if (status === "low") return "Eficiência baixa";
  return item.status_registro ?? "OK";
}
