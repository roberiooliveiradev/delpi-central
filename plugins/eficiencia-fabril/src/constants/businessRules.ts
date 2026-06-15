/** Faixa válida alinhada à API (`production_efficiency_valid_range`) — eficiência por tempos. */
export const PRODUCTION_EFFICIENCY_VALID_MIN_PCT = 0;
export const PRODUCTION_EFFICIENCY_VALID_MAX_PCT = 199;

/** Limite superior da faixa — apontamentos acima são «Verificar». */
export const VERIFY_EFFICIENCY_THRESHOLD_PCT = PRODUCTION_EFFICIENCY_VALID_MAX_PCT;

/** Abaixo deste valor (na faixa válida), o apontamento exige verificação de motivo. */
export const PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD = 50;

/** Abaixo deste valor, o KPI de eficiência é exibido em vermelho. */
export const EFFICIENCY_KPI_WARNING_PCT = 95;

/** Limite da API (`max_page_size`) para paginação em exportação. */
export const EFICIENCIA_FABRIL_MAX_PAGE_SIZE = 500;

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

export function isProductionEfficiencyLow(
  pct: number | null | undefined
): boolean {
  if (pct == null || Number.isNaN(pct) || isProductionEfficiencyOutlier(pct)) {
    return false;
  }
  return pct < PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD;
}
