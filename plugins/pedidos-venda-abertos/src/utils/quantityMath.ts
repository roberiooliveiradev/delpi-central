/** Casas decimais operacionais (milheiros). */
export const QUANTITY_DECIMALS = 3;

/** Metade da unidade mínima exibível (0,001) — resíduos abaixo disso são ignorados. */
export const QUANTITY_EPSILON = 0.0005;

const QUANTITY_SCALE = 10 ** QUANTITY_DECIMALS;

export function roundQuantity(value: number | null | undefined): number {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 0;
  }
  return Math.round(value * QUANTITY_SCALE) / QUANTITY_SCALE;
}

export function isNegligibleQuantity(value: number): boolean {
  return roundQuantity(value) <= 0;
}

export function isQuantityNeedSatisfied(remainingNeed: number): boolean {
  return remainingNeed <= QUANTITY_EPSILON;
}
