/** Faixa válida alinhada a OEE (H6_ZEFICI) e API (`production_efficiency_valid_range`). */
export const PRODUCTION_EFFICIENCY_VALID_MIN_PCT = 0;
export const PRODUCTION_EFFICIENCY_VALID_MAX_PCT = 199;

/** Limite superior da faixa — apontamentos acima são «Verificar». */
export const VERIFY_EFFICIENCY_THRESHOLD_PCT = PRODUCTION_EFFICIENCY_VALID_MAX_PCT;

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
