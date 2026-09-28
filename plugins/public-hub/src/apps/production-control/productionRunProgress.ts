export type ProductionRunProgress = {
  countedPieces: number;
  targetPieces: number;
  remainingPieces: number;
  progressPercent: number;
  visualPercent: number;
  targetReached: boolean;
  overproductionPieces: number;
};

export function resolveProductionRunProgress(
  piecesTotal: number,
  targetPieces: number | null | undefined,
): ProductionRunProgress | null {
  if (
    typeof targetPieces !== "number" ||
    !Number.isFinite(targetPieces) ||
    targetPieces <= 0
  ) {
    return null;
  }

  const countedPieces = Number.isFinite(piecesTotal) ? piecesTotal : 0;
  const progressPercent = (countedPieces / targetPieces) * 100;
  return {
    countedPieces,
    targetPieces,
    remainingPieces: countedPieces < targetPieces ? targetPieces - countedPieces : 0,
    progressPercent,
    visualPercent: progressPercent < 0 ? 0 : progressPercent > 100 ? 100 : progressPercent,
    targetReached: countedPieces >= targetPieces,
    overproductionPieces: countedPieces > targetPieces ? countedPieces - targetPieces : 0,
  };
}

/**
 * Converte peças absolutas do Pulse para a unidade de leitura do operador.
 * O fator vem da fila (api-delpi): MI usa 1000, então 3 peças viram 0,003.
 * Sem fator válido o valor é exibido em peças inteiras, sem conversão inventada.
 */
export function piecesToOperatorUnit(
  pieces: number,
  piecesConversionFactor: number | null | undefined,
): number {
  if (
    typeof piecesConversionFactor !== "number" ||
    !Number.isFinite(piecesConversionFactor) ||
    piecesConversionFactor <= 0
  ) {
    return pieces;
  }
  return pieces / piecesConversionFactor;
}
