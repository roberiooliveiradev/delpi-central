/** User-facing unit labels for market intelligence (PROC-0076 R5.S2).
 *
 * The producer owns the canonical ``unit`` label; this map is the
 * defensive MFE layer for raw unit codes that may still arrive from
 * older contracts or partial payloads. Presentation only — never a
 * unit conversion: codes and labels resolve 1:1 to the same physical
 * meaning (``usd_per_metric_ton`` IS ``US$/t``, not ``BRL/t``).
 */

const UNIT_DISPLAY_LABELS: Record<string, string> = {
  // Machine codes (external-data-api unit_code).
  usd_per_metric_ton: "US$/t",
  usd_per_pound: "US$/lb",
  metric_ton: "US$/t",
  brl_per_usd: "R$/US$",
  index: "Índice",
  number_index: "Índice",
  percent: "%",
  // Verbose labels still present in legacy fixtures/contracts.
  "USD/metric ton": "US$/t",
  "USD/lb": "US$/lb",
  "BRL per USD": "R$/US$",
  "número-índice": "Índice",
};

/** Friendly display label for a unit code/label — unknown values pass
 * through verbatim (honest, never silently dropped). */
export function formatMarketUnit(
  unit: string | null | undefined,
): string {
  if (!unit) return "";
  return UNIT_DISPLAY_LABELS[unit] ?? unit;
}
