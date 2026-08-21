/** Percentual faturado do card «a faturar até hoje» (0–100). */
export function billingDueInvoicedPercent(invoiced: number, total: number): number {
  const safeInvoiced = Math.max(0, Number(invoiced) || 0);
  const safeTotal = Math.max(0, Number(total) || 0);
  if (safeTotal <= 0) return 0;
  return Math.min(100, Math.round((safeInvoiced / safeTotal) * 100));
}
