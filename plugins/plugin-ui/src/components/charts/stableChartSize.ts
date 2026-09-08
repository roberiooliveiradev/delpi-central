/** Tamanho mínimo útil do host (px) — abaixo disso ainda está medindo. */
export const STABLE_CHART_MIN_SIZE_PX = 8;

/**
 * Delta mínimo (px) para aceitar resize — rejeita jitter de 1px
 * (scrollbar/flex/subpixel) que dispara React #185 no Recharts.
 */
export const STABLE_CHART_SIZE_EPSILON_PX = 2;

/**
 * Aceita novo tamanho só se o delta for ≥ epsilon.
 * Evita loop host↔chart (scrollbar/flex/subpixel) → React #185 no Recharts
 * (`ResponsiveContainer` + `notifyNestedSubs`) ao redimensionar a sidebar do portal.
 */
export function shouldAcceptMeasuredSize(
  prev: { w: number; h: number } | null,
  next: { w: number; h: number },
  epsilonPx = STABLE_CHART_SIZE_EPSILON_PX,
): boolean {
  if (next.w < STABLE_CHART_MIN_SIZE_PX || next.h < STABLE_CHART_MIN_SIZE_PX) {
    return false;
  }
  if (!prev) return true;
  return Math.abs(prev.w - next.w) >= epsilonPx || Math.abs(prev.h - next.h) >= epsilonPx;
}
