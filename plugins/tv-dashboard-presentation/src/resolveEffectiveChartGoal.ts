/**
 * Precedência da meta do gráfico: override manual finito → coluna projetada → null.
 */

export function resolveEffectiveChartGoal(args: {
  goalLineValue?: number | null;
  projectedGoal?: number | null;
}): number | null {
  const manual = args.goalLineValue;
  if (manual != null && Number.isFinite(Number(manual))) {
    return Number(manual);
  }
  const projected = args.projectedGoal;
  if (projected != null && Number.isFinite(Number(projected))) {
    return Number(projected);
  }
  return null;
}
