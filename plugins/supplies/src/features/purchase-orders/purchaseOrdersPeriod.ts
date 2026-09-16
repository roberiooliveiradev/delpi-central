import {
  matchPeriodPreset,
  PERIOD_PRESET_OPTIONS,
  resolvePeriodPreset,
  type PeriodPresetId,
  type PeriodPresetRange,
} from "../../app/periodPreset";

/**
 * PO-local period chip: shared presets + unbounded (no delivery-date filter).
 * Does not extend Overview/PR periodPreset — empty dates mean «all open POs».
 */
export const PURCHASE_ORDERS_UNBOUNDED_PERIOD = "unbounded" as const;

export type PurchaseOrdersPeriodId =
  | typeof PURCHASE_ORDERS_UNBOUNDED_PERIOD
  | PeriodPresetId;

export const PURCHASE_ORDERS_PERIOD_OPTIONS: {
  value: PurchaseOrdersPeriodId;
  label: string;
}[] = [
  { value: PURCHASE_ORDERS_UNBOUNDED_PERIOD, label: "Sem filtro" },
  ...PERIOD_PRESET_OPTIONS,
];

/**
 * Derive chip from URL/query dates (no dedicated period query param).
 * Both empty → Sem filtro. Otherwise reuse shared match (incl. Personalizado).
 */
export function matchPurchaseOrdersPeriod(
  from: string,
  to: string,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): PurchaseOrdersPeriodId {
  const fromTrim = (from || "").trim();
  const toTrim = (to || "").trim();
  if (!fromTrim && !toTrim) return PURCHASE_ORDERS_UNBOUNDED_PERIOD;
  return matchPeriodPreset(fromTrim, toTrim, now, timeZone);
}

export function resolvePurchaseOrdersPeriod(
  period: PurchaseOrdersPeriodId,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): PeriodPresetRange | null | "unbounded" {
  if (period === PURCHASE_ORDERS_UNBOUNDED_PERIOD) return "unbounded";
  if (period === "custom") return null;
  return resolvePeriodPreset(period, now, timeZone);
}
