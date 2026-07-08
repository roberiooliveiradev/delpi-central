import {
  clampImpactEffortScore,
  resolveImpactEffortQuadrant,
  type ImpactEffortPoint,
  type ImpactEffortQuadrant,
} from "./impactEffortTypes";

const THRESHOLD_EPSILON = 0.05;
const QUADRANT_NUDGE = 3;

/** Desloca levemente pontos sobre as linhas de limiar para ficarem dentro do quadrante. */
export function resolveDisplayScores(
  impacto: number,
  esforco: number,
  quadrante: ImpactEffortQuadrant | undefined,
  threshold: number,
): { impacto: number; esforco: number } {
  const impact = clampImpactEffortScore(impacto);
  const effort = clampImpactEffortScore(esforco);
  const quadrant = quadrante ?? resolveImpactEffortQuadrant(impact, effort, threshold);

  const onImpactThreshold = Math.abs(impact - threshold) <= THRESHOLD_EPSILON;
  const onEffortThreshold = Math.abs(effort - threshold) <= THRESHOLD_EPSILON;

  if (!onImpactThreshold && !onEffortThreshold) {
    return { impacto: impact, esforco: effort };
  }

  let deltaImpact = 0;
  let deltaEffort = 0;

  switch (quadrant) {
    case "quick_win":
      if (onImpactThreshold) deltaImpact = QUADRANT_NUDGE;
      if (onEffortThreshold) deltaEffort = -QUADRANT_NUDGE;
      break;
    case "strategic":
      if (onImpactThreshold) deltaImpact = QUADRANT_NUDGE;
      if (onEffortThreshold) deltaEffort = QUADRANT_NUDGE;
      break;
    case "fill_in":
      if (onImpactThreshold) deltaImpact = -QUADRANT_NUDGE;
      if (onEffortThreshold) deltaEffort = -QUADRANT_NUDGE;
      break;
    case "rethink":
      if (onImpactThreshold) deltaImpact = -QUADRANT_NUDGE;
      if (onEffortThreshold) deltaEffort = QUADRANT_NUDGE;
      break;
  }

  return {
    impacto: clampImpactEffortScore(impact + deltaImpact),
    esforco: clampImpactEffortScore(effort + deltaEffort),
  };
}

export function resolveActivePoint(
  points: ImpactEffortPoint[],
  activePointId?: string | null,
): ImpactEffortPoint | undefined {
  if (!activePointId) return undefined;
  return points.find((point) => point.id === activePointId);
}
