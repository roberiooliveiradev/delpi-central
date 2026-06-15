import type { MultiSelectOption } from "../components/MultiSelectField";
import {
  PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD,
  PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
  PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
} from "./businessRules";
import { resolveEficienciaFabrilAppointmentStatus } from "../utils/appointmentStatus";
import type { EficienciaFabrilItem } from "../types/eficienciaFabril";

export type EficienciaFabrilEfficiencyBand = "verify" | "low" | "ok";

export const EFFICIENCY_BAND_FILTER_OPTIONS: MultiSelectOption[] = [
  {
    value: "ok",
    label: `Na faixa (${PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD}%–${PRODUCTION_EFFICIENCY_VALID_MAX_PCT}%)`,
  },
  {
    value: "low",
    label: `Eficiência baixa (< ${PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD}%)`,
  },
  {
    value: "verify",
    label: `Fora da faixa (${PRODUCTION_EFFICIENCY_VALID_MIN_PCT}–${PRODUCTION_EFFICIENCY_VALID_MAX_PCT}%+)`,
  },
];

export function matchesEfficiencyBandFilter(
  item: Pick<EficienciaFabrilItem, "eficiencia_percentual" | "status_registro">,
  bands: EficienciaFabrilEfficiencyBand[] | undefined
): boolean {
  if (!bands || bands.length === 0) return true;
  const status = resolveEficienciaFabrilAppointmentStatus(item);
  return bands.includes(status);
}
