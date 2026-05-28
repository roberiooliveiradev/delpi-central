import type { AlertsDashboardViewData } from "../types/alerts";
import type { DepartmentDetailsViewData } from "../types/departmentDetails";
import type { DepartmentOverviewViewItem } from "../types/departments";
import type { ExecutiveDashboardViewData } from "../types/executiveSummary";
import type {
  GoalMode,
  IndicatorViewItem,
  MonthlyTargetItem,
  PerformanceDirection,
} from "../types/indicators";
import type { TrendsDashboardViewData } from "../types/trends";
import {
  buildPresentationViewData,
  type PresentationViewData,
} from "../types/presentation";
import type { StrategicIndicatorsPresentationApiResponse } from "../api/strategicIndicatorsPresentationApi";

export type PresentationWarningItem = {
  source: string;
  message: string;
};

type AdaptPresentationPayloadParams = {
  payload: StrategicIndicatorsPresentationApiResponse;
  focusDepartmentId?: string | null;
};

type IndicatorValueFormatFields = {
  valueUnit: string | null;
  valuePrefix: string | null;
  valueSuffix: string | null;
  valueDecimals: number;
};

function slugify(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function buildId(
  prefix: string,
  ...parts: Array<string | number | undefined | null>
) {
  const normalized = parts
    .filter((part) => part !== undefined && part !== null && String(part).trim() !== "")
    .map((part) => slugify(String(part)));

  return [prefix, ...normalized].join("-");
}

function normalizeDirection(
  value: string | null | undefined,
): "up" | "down" | "stable" {
  if (value === "up" || value === "down" || value === "stable") {
    return value;
  }

  return "stable";
}

function normalizeGoalMode(value: string | null | undefined): GoalMode {
  return value === "monthly_curve" ? "monthly_curve" : "standard";
}

function normalizePerformanceDirection(
  value: string | null | undefined,
): PerformanceDirection {
  return value === "lower_is_better" ? "lower_is_better" : "higher_is_better";
}

function normalizeMonthlyTargets(
  value: Array<{ month_number: number; target_value: number }> | undefined | null,
): MonthlyTargetItem[] {
  return (value ?? []).map((item) => ({
    month_number: item.month_number,
    target_value: item.target_value,
  }));
}

function normalizeAggregationMode(
  value: string | null | undefined,
): "average_of_units" | "consolidated" | "mixed_scope" {
  if (
    value === "average_of_units" ||
    value === "consolidated" ||
    value === "mixed_scope"
  ) {
    return value;
  }

  return "consolidated";
}

function getValueFormatFields(source: unknown): IndicatorValueFormatFields {
  const item = source as {
    value_unit?: string | null;
    value_prefix?: string | null;
    value_suffix?: string | null;
    value_decimals?: number | string | null;
  };

  const parsedDecimals = Number(item.value_decimals ?? 2);

  return {
    valueUnit: item.value_unit ?? null,
    valuePrefix: item.value_prefix ?? null,
    valueSuffix: item.value_suffix ?? null,
    valueDecimals: Number.isFinite(parsedDecimals) ? parsedDecimals : 2,
  };
}

function buildExecutiveSummary(
  payload: StrategicIndicatorsPresentationApiResponse,
): ExecutiveDashboardViewData {
  return {
    competence: payload.executive_summary.competence,
    igd: payload.executive_summary.igd,
    igdExact: payload.executive_summary.igd_exact,
    classification: payload.executive_summary.classification,
    variation: {
      value: payload.executive_summary.variation.value,
      direction: normalizeDirection(payload.executive_summary.variation.direction),
      vsLabel: payload.executive_summary.variation.vs_label,
    },
    departments: payload.executive_summary.departments.map((department) => ({
      id: department.id,
      name: department.name,
      shortName: department.short_name,
      weightPct: department.weight_pct,
      score: department.score,
      contribution: department.contribution,
      trend: normalizeDirection(department.trend),
      strategicSummary: department.strategic_summary,
      keyIndicators: department.key_indicators,
      executiveGoal: department.executive_goal,
      variation: {
        value: department.variation.value,
        direction: normalizeDirection(department.variation.direction),
      },
    })),
    alertsSummary: payload.executive_summary.alerts_summary.map((alert, index) => ({
      id: buildId("executive-summary-alert", index, alert.severity, alert.title),
      title: alert.title,
      severity: alert.severity,
      impact: alert.impact,
      recommendation: alert.recommendation,
    })),
  };
}

function buildAlerts(
  payload: StrategicIndicatorsPresentationApiResponse,
): AlertsDashboardViewData {
  return {
    competence: payload.alerts.competence,
    igdClassification: payload.executive_summary.classification,
    executiveAlerts: payload.alerts.executive_alerts.map((alert, index) => ({
      id: buildId("executive-alert", index, alert.severity, alert.title),
      title: alert.title,
      severity: alert.severity,
      impact: alert.impact,
      recommendation: alert.recommendation,
    })),
    departmentAlerts: payload.alerts.department_alerts.map((alert) => {
      const currentScore = Number(alert.score ?? 0);
      const previousScore = Number(alert.previous_score ?? currentScore);
      const variation = Number(alert.variation ?? currentScore - previousScore);

      return {
        id: buildId(
          "department-alert",
          alert.department_id,
          alert.severity,
          alert.message,
        ),
        departmentName: alert.department_name,
        currentScore,
        previousScore,
        variation,
        severity: alert.severity,
        reason: alert.message,
        recommendation: "Priorizar plano de ação do departamento no curto prazo.",
      };
    }),
    indicatorAlerts: payload.alerts.indicator_alerts.map((alert) => ({
      id: buildId(
        "indicator-alert",
        alert.department_id,
        alert.indicator_id,
        alert.severity,
      ),
      departmentName: alert.department_name,
      indicatorName: alert.indicator_name,
      simulatedScore: alert.score,
      goalLabel: alert.goal_label ?? "Meta não informada",
      goalValue: alert.goal_value ?? null,
      goalPeriodicity: alert.goal_periodicity ?? null,
      goalMode: normalizeGoalMode(alert.goal_mode),
      monthlyTargets: normalizeMonthlyTargets(alert.monthly_targets),
      goals: alert.goals ?? {},
      performanceDirection: normalizePerformanceDirection(
        alert.performance_direction,
      ),
      ...getValueFormatFields(alert),
      severity: alert.severity,
      reason: alert.message,
      recommendation: "Atuar na causa do indicador e monitorar no próximo fechamento.",
    })),
    partialSuccess: payload.alerts.partial_success,
    errors: (payload.alerts.errors ?? []).map((error) => ({
      departmentId: error.department_id ?? "",
      source: error.source ?? "",
      message: error.message,
    })),
  };
}

function buildDepartmentsOverview(
  payload: StrategicIndicatorsPresentationApiResponse,
): DepartmentOverviewViewItem[] {
  return payload.departments_overview.map((department) => ({
    id: department.id,
    name: department.name,
    shortName: department.short_name,
    weightInIgd: department.weight_pct,
    score: department.score,
    classification: department.classification,
    contribution: department.contribution,
    aggregationMode: normalizeAggregationMode(department.aggregation_mode),
    strategicSummary: department.strategic_summary,
    variation: {
      value: department.variation.value,
      direction: normalizeDirection(department.variation.direction),
    },
  }));
}

function buildDepartmentDetailsById(
  payload: StrategicIndicatorsPresentationApiResponse,
): Record<string, DepartmentDetailsViewData> {
  return Object.fromEntries(
    Object.entries(payload.department_details_by_id).map(([departmentId, details]) => [
      departmentId,
      {
        id: details.id,
        name: details.name,
        shortName: details.short_name,
        weightInIgd: details.weight_pct,
        score: details.score,
        classification: details.classification,
        contribution: details.contribution,
        aggregationMode: normalizeAggregationMode(details.aggregation_mode),
        strategicSummary: details.strategic_summary,
        variation: {
          value: details.variation.value,
          direction: normalizeDirection(details.variation.direction),
        },
        units: details.units.map((unit) => ({
          unitId: unit.unit_id,
          unitName: unit.unit_name,
          score: unit.score,
          hasValue: unit.has_value,
          classification: unit.classification,
        })),
        indicators: details.indicators.map((indicator) => ({
          id: indicator.id,
          name: indicator.name,
          weightPct: indicator.weight_pct,
          goalLabel: indicator.goal_label,
          goalValue: indicator.goal_value,
          goalPeriodicity: indicator.goal_periodicity,
          goalMode: normalizeGoalMode(indicator.goal_mode),
          monthlyTargets: normalizeMonthlyTargets(indicator.monthly_targets),
          strategicDescription: indicator.strategic_description,
          scopeType: indicator.scope_type,
          performanceDirection: normalizePerformanceDirection(
            indicator.performance_direction,
          ),
          realized: indicator.realized ?? {},
          hasValue: indicator.has_value,
          score: indicator.score,
          gap: indicator.gap,
          goals: indicator.goals ?? {},
          gaps: indicator.gaps ?? {},
          trend: normalizeDirection(indicator.trend),
          classification: indicator.classification,
          ...getValueFormatFields(indicator),
        })),
      },
    ]),
  );
}

function buildIndicatorsByDepartmentId(
  payload: StrategicIndicatorsPresentationApiResponse,
): Record<string, IndicatorViewItem[]> {
  return Object.fromEntries(
    Object.entries(payload.indicators_by_department_id).map(
      ([departmentId, indicators]) => [
        departmentId,
        indicators.map((indicator) => ({
          id: indicator.indicator_id,
          name: indicator.indicator_name,
          departmentId: indicator.department_id,
          departmentName: indicator.department_name,
          weightPct: indicator.weight_pct,
          goalLabel: indicator.goal_label,
          goalValue: indicator.goal_value,
          goalPeriodicity: indicator.goal_periodicity,
          goalMode: normalizeGoalMode(indicator.goal_mode),
          monthlyTargets: normalizeMonthlyTargets(indicator.monthly_targets),
          value: indicator.value,
          realized: indicator.realized ?? {},
          score: indicator.score,
          gap: indicator.gap,
          goals: indicator.goals ?? {},
          gaps: indicator.gaps ?? {},
          hasValue: indicator.has_value ?? indicator.value !== null,
          trend: normalizeDirection(indicator.trend),
          classification: indicator.classification,
          scopeType: indicator.scope_type,
          performanceDirection: normalizePerformanceDirection(
            indicator.performance_direction,
          ),
          source: indicator.source,
          ...getValueFormatFields(indicator),
        })),
      ],
    ),
  );
}

function buildDepartmentSeries(
  department: StrategicIndicatorsPresentationApiResponse["trends"]["departments"][number],
) {
  if (department.series?.length) {
    return department.series.map((point) => ({
      period: point.period,
      score: point.score,
      classification: point.classification,
      contribution: point.contribution,
    }));
  }

  return [
    {
      period: "Anterior",
      score: department.previous,
    },
    {
      period: "Atual",
      score: department.current,
    },
  ];
}

function buildIndicatorSeriesByDepartmentId(
  payload: StrategicIndicatorsPresentationApiResponse,
): TrendsDashboardViewData["indicatorSeriesByDepartmentId"] {
  const rawIndicatorSeriesByDepartmentId =
    payload.trends.indicator_series_by_department_id;

  if (!rawIndicatorSeriesByDepartmentId) {
    return {};
  }

  return Object.fromEntries(
    Object.entries(rawIndicatorSeriesByDepartmentId).map(([departmentId, items]) => [
      departmentId,
      (items ?? []).map((item) => ({
        indicatorId: item.indicator_id,
        indicatorName: item.indicator_name,
        weightPct: item.weight_pct,
        goalLabel: item.goal_label,
        goalValue: item.goal_value,
        goalPeriodicity: item.goal_periodicity,
        goalMode: item.goal_mode ?? "standard",
        monthlyTargets: (item.monthly_targets ?? []).map((target) => ({
          monthNumber: target.month_number,
          targetValue: target.target_value,
        })),
        scopeType: item.scope_type,
        performanceDirection: item.performance_direction,
        strategicDescription: item.strategic_description,
        source: item.source,
        ...getValueFormatFields(item),
        series: (item.series ?? []).map((point) => ({
          period: point.period,
          value: point.value,
          score: point.score,
          gap: point.gap,
          classification: point.classification,
          trend: normalizeDirection(point.trend),
        })),
      })),
    ]),
  );
}

function buildTrends(
  payload: StrategicIndicatorsPresentationApiResponse,
): TrendsDashboardViewData {
  return {
    competence: payload.trends.competence,
    currentIgd: payload.trends.current_igd,
    previousIgd: payload.trends.previous_igd,
    currentClassification: payload.trends.current_classification,
    igdSeries: payload.trends.igd_series.map((point) => ({
      period: point.period,
      value: point.value,
      classification: point.classification,
    })),
    departments: payload.trends.departments.map((department) => ({
      id: department.id,
      name: department.name,
      current: department.current,
      previous: department.previous,
      direction: normalizeDirection(department.direction),
      lastStepDirection: normalizeDirection(
        department.last_step_direction ?? department.direction,
      ),
      netVariation: department.net_variation ?? department.current - department.previous,
      bestScore:
        department.best_score ?? Math.max(department.current, department.previous),
      worstScore:
        department.worst_score ?? Math.min(department.current, department.previous),
      currentClassification: department.current_classification,
      currentContribution: department.current_contribution,
      series: buildDepartmentSeries(department),
    })),
    indicatorSeriesByDepartmentId: buildIndicatorSeriesByDepartmentId(payload),
    errors: (payload.trends.errors ?? []).map((error) => ({
      competence: error.competence ?? "",
      departmentId: error.department_id ?? "",
      source: error.source ?? "",
      message: error.message,
    })),
    partialSuccess: payload.trends.partial_success,
  };
}

export function adaptPresentationPayloadToViewData({
  payload,
  focusDepartmentId,
}: AdaptPresentationPayloadParams): PresentationViewData {
  const executiveSummary = buildExecutiveSummary(payload);
  const alerts = buildAlerts(payload);
  const departmentsOverview = buildDepartmentsOverview(payload);
  const departmentDetailsById = buildDepartmentDetailsById(payload);
  const indicatorsByDepartmentId = buildIndicatorsByDepartmentId(payload);
  const trends = buildTrends(payload);

  return buildPresentationViewData({
    executiveSummary,
    executiveAlerts: alerts.executiveAlerts,
    alerts,
    departmentsOverview,
    departmentDetailsById,
    indicatorsByDepartmentId,
    trends,
    focusDepartmentId,
  });
}

export function adaptPresentationWarnings(
  payload: StrategicIndicatorsPresentationApiResponse,
): PresentationWarningItem[] {
  return (payload.meta.errors ?? []).map((error, index) => ({
    source: error.source || error.scope || `presentation-${index}`,
    message: error.message,
  }));
}