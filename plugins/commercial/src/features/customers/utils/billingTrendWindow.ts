/** Janela configurável da tendência de faturamento (Minha Carteira). */

export const BILLING_TREND_WINDOW_PRESETS = [7, 30, 90] as const;

export type BillingTrendWindowPreset = (typeof BILLING_TREND_WINDOW_PRESETS)[number] | "custom";

export const DEFAULT_BILLING_TREND_WINDOW_DAYS = 30;
export const MIN_BILLING_TREND_WINDOW_DAYS = 1;
export const MAX_BILLING_TREND_WINDOW_DAYS = 365;

export function clampBillingTrendWindowDays(value: number | null | undefined): number {
  if (value == null || !Number.isFinite(value)) {
    return DEFAULT_BILLING_TREND_WINDOW_DAYS;
  }
  const days = Math.trunc(value);
  if ((BILLING_TREND_WINDOW_PRESETS as readonly number[]).includes(days)) {
    return days;
  }
  return Math.max(
    MIN_BILLING_TREND_WINDOW_DAYS,
    Math.min(MAX_BILLING_TREND_WINDOW_DAYS, days),
  );
}

export function billingTrendWindowLabel(days: number): string {
  const n = clampBillingTrendWindowDays(days);
  if (n === 7) return "7 dias";
  if (n === 30) return "30 dias";
  if (n === 90) return "90 dias";
  return `${n} dias`;
}
