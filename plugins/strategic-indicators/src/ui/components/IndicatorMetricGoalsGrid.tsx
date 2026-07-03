import type { ReactNode } from "react";
import {
  formatIndicatorGapDisplay,
  formatIndicatorGoalValue,
  formatIndicatorRealizedDisplay,
  formatIndicatorScore,
  type IndicatorDisplayContext,
  type IndicatorGoalDisplayInput,
  type IndicatorScopedMetricsInput,
  type IndicatorValueFormat,
} from "../shared/indicatorValueFormatter";
import {
  resolveIndicatorMetricLayout,
  resolveIndicatorMetricLayoutClass,
} from "../shared/resolveIndicatorMetricLayout";
import { ScopeMetricBadges } from "./ScopeMetricBadges";
import "./IndicatorMetricGoalsGrid.css";

export type IndicatorMetricGoalsSource = IndicatorScopedMetricsInput &
  IndicatorGoalDisplayInput & {
    hasValue?: boolean;
    score?: number | null;
  };

type IndicatorMetricGoalsGridProps = {
  indicator: IndicatorMetricGoalsSource;
  competence?: string | null;
  displayContext?: IndicatorDisplayContext;
  scoreLabel?: string;
  className?: string;
};

function getValueFormat(indicator: IndicatorMetricGoalsSource): IndicatorValueFormat {
  return {
    valueUnit: indicator.valueUnit,
    valuePrefix: indicator.valuePrefix,
    valueSuffix: indicator.valueSuffix,
    valueDecimals: indicator.valueDecimals,
  };
}

function MetricGoalCell({
  label,
  missing,
  children,
}: {
  label: string;
  missing?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="si-indicator-card__goal">
      <span className="si-indicator-card__goal-label">{label}</span>
      <strong
        className={`si-indicator-card__goal-value${
          missing ? " si-indicator-card__goal-value--missing" : ""
        }`}
      >
        {children}
      </strong>
    </div>
  );
}

export function IndicatorMetricGoalsGrid({
  indicator,
  competence,
  displayContext,
  scoreLabel = "Nota",
  className,
}: IndicatorMetricGoalsGridProps) {
  const valueFormat = getValueFormat(indicator);
  const layout = resolveIndicatorMetricLayout(
    {
      goals: indicator.goals,
      realized: indicator.realized,
      gaps: indicator.gaps,
    },
    { activeBranch: displayContext?.activeBranch },
  );
  const layoutClass = resolveIndicatorMetricLayoutClass(layout);
  const missingValue = !indicator.hasValue;

  return (
    <div
      className={`si-indicator-metric-goals ${layoutClass}${className ? ` ${className}` : ""}`}
    >
      <MetricGoalCell label="Meta">
        <ScopeMetricBadges
          values={indicator.goals}
          format={valueFormat}
          displayContext={displayContext}
          layout="compact"
          emptyLabel={formatIndicatorGoalValue(indicator, competence, displayContext)}
        />
      </MetricGoalCell>

      <MetricGoalCell label="Realizado" missing={missingValue}>
        <ScopeMetricBadges
          values={indicator.realized}
          format={valueFormat}
          displayContext={displayContext}
          layout="compact"
          emptyLabel={formatIndicatorRealizedDisplay(
            indicator,
            valueFormat,
            displayContext,
          )}
        />
      </MetricGoalCell>

      <MetricGoalCell label={scoreLabel} missing={missingValue}>
        <span className="si-indicator-card__goal-value--score">
          {formatIndicatorScore(indicator.score)}
        </span>
      </MetricGoalCell>

      <MetricGoalCell label="Gap" missing={missingValue}>
        <ScopeMetricBadges
          values={indicator.gaps}
          format={valueFormat}
          displayContext={displayContext}
          layout="compact"
          emptyLabel={formatIndicatorGapDisplay(
            indicator,
            valueFormat,
            displayContext,
          )}
        />
      </MetricGoalCell>
    </div>
  );
}
