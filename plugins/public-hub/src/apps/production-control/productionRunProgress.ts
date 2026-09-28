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
