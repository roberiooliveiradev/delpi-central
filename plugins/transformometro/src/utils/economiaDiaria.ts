/** Economia líquida diária proporcional à economia bruta diária já calculada na API. */
export function economiaLiquidaDiaria(item: {
  economia_bruta?: number;
  economia_liquida_mes?: number;
  economia_diaria?: number | null;
}): number {
  const bruta = item.economia_bruta ?? 0;
  const liquida = item.economia_liquida_mes ?? 0;
  const diariaBruta = item.economia_diaria ?? 0;
  if (bruta <= 0 || diariaBruta <= 0) return 0;
  return (liquida / bruta) * diariaBruta;
}
