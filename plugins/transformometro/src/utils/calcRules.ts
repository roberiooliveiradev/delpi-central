/**
 * Espelho documental das regras em transformometro-api/tm_app/domain/calc_rules.py.
 * O dashboard consome valores já calculados pela API (horas_diaria, economia_diaria).
 */

export type PeriodTotalsLike = {
  economia_bruta?: number;
  economia_diaria?: number | null;
  horas_economizadas_mes?: number;
  horas_diaria?: number | null;
};

/** Média diária de horas no recorte — preferir horas_diaria da API. */
export function horasEconomizadasDiaria(item: PeriodTotalsLike): number {
  if (item.horas_diaria != null && Number.isFinite(item.horas_diaria)) {
    return item.horas_diaria;
  }

  const bruta = item.economia_bruta ?? 0;
  const diariaBruta = item.economia_diaria ?? 0;
  const horasMes = item.horas_economizadas_mes ?? 0;
  if (bruta <= 0 || diariaBruta <= 0 || horasMes <= 0) return 0;

  return (horasMes / bruta) * diariaBruta;
}
