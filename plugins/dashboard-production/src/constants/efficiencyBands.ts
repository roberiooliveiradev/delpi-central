import type { MultiSelectOption } from "../components/MultiSelectField";
import {
  PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD,
  PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
  PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
} from "./businessRules";

export type ProductionEfficiencyBand = "verify" | "low" | "ok";

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

export function formatEfficiencyBandsQuery(
  bands: ProductionEfficiencyBand[] | undefined
): string | undefined {
  if (!bands || bands.length === 0) return undefined;
  return bands.join(",");
}
