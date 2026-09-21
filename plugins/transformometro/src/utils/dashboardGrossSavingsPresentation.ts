import {
  buildKpiGoalPresentation,
  buildSiIndicatorScoreMap,
  pickSiIddScoreLabel,
  type DashboardGoalFields,
  type KpiGoalPresentation,
} from "@delpi/plugin-ui/index";

import { STRATEGIC_INDICATORS_GROSS_SAVINGS_INDICATOR_ID } from "../constants/strategicIndicatorsContext";
import type { DashboardStrategicIndicators } from "../data/api/transformometroApi";

export function buildGrossSavingsGoalFields(
  si: DashboardStrategicIndicators | null | undefined,
): DashboardGoalFields | null {
  const goal = si?.gross_savings;
  if (!goal?.has_goal && goal?.comparable_goal == null && goal?.reference_goal == null) {
    return null;
  }
  return goal;
}

export function buildGrossSavingsKpiPresentation(
  contextLabel: string,
  si: DashboardStrategicIndicators | null | undefined,
  realizedValue: number | null | undefined,
  dateStart: string,
  dateEnd: string,
): KpiGoalPresentation {
  const scoresById = buildSiIndicatorScoreMap(si?.indicators);
  const iddScoreLabel = pickSiIddScoreLabel(
    scoresById,
    STRATEGIC_INDICATORS_GROSS_SAVINGS_INDICATOR_ID,
  );
  return buildKpiGoalPresentation(contextLabel, buildGrossSavingsGoalFields(si), undefined, {
    realizedValue,
    dateStart,
    dateEnd,
    iddScoreLabel,
    showGoal: Boolean(si?.available && buildGrossSavingsGoalFields(si)),
  });
}
