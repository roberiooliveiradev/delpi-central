import type {
  AlertsDashboardViewData,
  DepartmentAlertViewItem,
  ExecutiveAlertViewItem,
  IndicatorAlertViewItem,
} from "./alerts";
import type { DepartmentDetailsViewData } from "./departmentDetails";
import type { DepartmentOverviewViewItem } from "./departments";
import type { ExecutiveDashboardViewData } from "./executiveSummary";
import type { IndicatorViewItem } from "./indicators";
import type {
  DepartmentTrendSeriesPoint,
  IndicatorTrendSeriesItem,
  TrendsDashboardViewData,
} from "./trends";
import {
  getAggregationModeLabel,
  getGoalModeLabel,
  getGoalPeriodicityLabel,
  getPerformanceDirectionLabel,
  getScopeTypeLabel,
  getSeverityLabel,
  getTrendLabel,
} from "../../ui/presentation/labels";

export type PresentationSparklinePoint = {
  period: string;
  value: number;
  classification?: string;
  contribution?: number;
};

export type PresentationIndicatorSeriesPoint = {
  period: string;
  value: number;
  score: number;
  gap: number;
  classification?: string;
  trend: "up" | "down" | "stable";
};

export type PresentationDepartmentBoardItem = {
  id: string;
  name: string;
  current: number;
  previous: number;
  direction: "up" | "down" | "stable";
  directionLabel: string;
  series: PresentationSparklinePoint[];
  netVariation: number;
  bestScore: number;
  worstScore: number;
  currentClassification?: string;
  currentContribution?: number;
  lastStepDirection?: "up" | "down" | "stable";
};

export type PresentationKpiCard = {
  id: string;
  label: string;
  value: string;
  support?: string;
};

export type PresentationDepartmentSnapshot = {
  id: string;
  name: string;
  shortName: string;
  score: number;
  classification: string;
  contribution: number;
  weightInIgd: number;
  strategicSummary: string;
  variation: {
    value: number;
    direction: "up" | "down" | "stable";
    directionLabel: string;
  };
};

export type PresentationDepartmentIndicatorSnapshot = {
  id: string;
  name: string;
  weightPct: number;
  goalLabel: string;
  goalValue: number;
  goalPeriodicity: string;
  goalMode: string;
  monthlyTargets: Array<{
    monthNumber: number;
    targetValue: number;
  }>;
  strategicDescription: string;
  scopeType: string;
  performanceDirection: string;
  currentValue: number | null;
  realized: Record<string, number | null>;
  hasValue: boolean;
  score: number | null;
  gap: number | null;
  gaps: Record<string, number | null>;
  trend: "up" | "down" | "stable";
  trendLabel: string;
  valueUnit: string | null;
  valuePrefix: string | null;
  valueSuffix: string | null;
  valueDecimals: number;
  series?: PresentationIndicatorSeriesPoint[];
};

export type PresentationDepartmentFocus = {
  id: string;
  name: string;
  shortName: string;
  weightInIgd: number;
  score: number;
  classification: string;
  contribution: number;
  aggregationMode: string;
  strategicSummary: string;
  variation: {
    value: number;
    direction: "up" | "down" | "stable";
    directionLabel: string;
  };
  units: Array<{
    id: string;
    name: string;
    score: number | null;
    hasValue: boolean;
    classification: string;
  }>;
  indicators: PresentationDepartmentIndicatorSnapshot[];
  series?: PresentationSparklinePoint[];
};

export type PresentationTrendSnapshot = {
  competence: string;
  currentIgd: number;
  previousIgd: number;
  currentClassification: string;
  igdSeries: Array<{
    period: string;
    value: number;
  }>;
  departments: PresentationDepartmentBoardItem[];
  indicatorSeriesByDepartmentId: Record<string, IndicatorTrendSeriesItem[]>;
  partialSuccess: boolean;
  errors: Array<{
    competence: string;
    departmentId: string;
    source: string;
    message: string;
  }>;
};

export type PresentationAlertSnapshot = {
  igdClassification: string;
  executive: Array<
    ExecutiveAlertViewItem & {
      severityLabel: string;
    }
  >;
  departments: Array<
    DepartmentAlertViewItem & {
      severityLabel: string;
    }
  >;
  indicators: Array<
    IndicatorAlertViewItem & {
      severityLabel: string;
      goalModeLabel: string;
      performanceDirectionLabel: string;
    }
  >;
  partialSuccess: boolean;
  errors: Array<{
    departmentId: string;
    source: string;
    message: string;
  }>;
};

export type PresentationViewData = {
  competence: string;
  igd: number;
  igdExact: number;
  classification: string;
  trendLabel: string;
  currentIgd: number;
  previousIgd: number;
  variationValue: number;
  variationDirection: "up" | "down" | "stable";
  variationDirectionLabel: string;
  topDepartment: string;
  topRisk: string;
  currentPeriod: string;
  previousPeriod: string;
  departments: PresentationDepartmentBoardItem[];
  executiveAlerts: ExecutiveAlertViewItem[];
  kpis: PresentationKpiCard[];
  departmentsOverview: PresentationDepartmentSnapshot[];
  departmentFocus: PresentationDepartmentFocus | null;
  trend: PresentationTrendSnapshot | null;
  alerts: PresentationAlertSnapshot;
};

function normalizeDirection(
  value: string | null | undefined,
): "up" | "down" | "stable" {
  if (value === "up" || value === "down" || value === "stable") {
    return value;
  }

  return "stable";
}

function getPresentationTrendLabel(
  direction: "up" | "down" | "stable",
): string {
  if (direction === "up") return "Melhora no período";
  if (direction === "down") return "Queda no período";
  return "Estabilidade no período";
}

function buildPreviousCompetence(competence: string): string {
  const [yearStr, monthStr] = competence.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);

  if (!year || !month) {
    return competence;
  }

  if (month === 1) {
    return `${year - 1}-12`;
  }

  return `${year}-${String(month - 1).padStart(2, "0")}`;
}

function mapTrendSeriesToSparklinePoints(
  series: DepartmentTrendSeriesPoint[],
): PresentationSparklinePoint[] {
  return series.map((point) => ({
    period: point.period,
    value: point.score,
    classification: point.classification,
    contribution: point.contribution,
  }));
}

function mapIndicatorSeries(
  item: IndicatorTrendSeriesItem | undefined,
): PresentationIndicatorSeriesPoint[] | undefined {
  if (!item?.series?.length) return undefined;

  return item.series.map((point) => ({
    period: point.period,
    value: point.value,
    score: point.score,
    gap: point.gap,
    classification: point.classification,
    trend: normalizeDirection(point.trend),
  }));
}

function formatNumber(value: number, fractionDigits = 1): string {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

function buildExecutiveKpis(
  executiveSummary: ExecutiveDashboardViewData,
  trends: TrendsDashboardViewData | null,
): PresentationKpiCard[] {
  const departments = executiveSummary.departments ?? [];
  const strongest = [...departments].sort((a, b) => b.score - a.score)[0];
  const weakest = [...departments].sort((a, b) => a.score - b.score)[0];

  return [
    {
      id: "igd-current",
      label: "IGD atual",
      value: formatNumber(executiveSummary.igd, 1),
      support: executiveSummary.classification,
    },
    {
      id: "igd-variation",
      label: "Variação",
      value: `${executiveSummary.variation.value > 0 ? "+" : ""}${formatNumber(
        executiveSummary.variation.value,
        1,
      )}`,
      support: getTrendLabel(executiveSummary.variation.direction),
    },
    {
      id: "top-department",
      label: "Melhor departamento",
      value: strongest?.name ?? "—",
      support: strongest ? formatNumber(strongest.score, 1) : undefined,
    },
    {
      id: "risk-department",
      label: "Maior atenção",
      value: weakest?.name ?? "—",
      support: weakest ? formatNumber(weakest.score, 1) : undefined,
    },
    {
      id: "period-window",
      label: "Janela analisada",
      value: `${trends?.igdSeries.length ?? 1} período(s)`,
      support: executiveSummary.competence,
    },
  ];
}

function buildDepartmentBoard(
  executiveSummary: ExecutiveDashboardViewData,
  trends: TrendsDashboardViewData | null,
): PresentationDepartmentBoardItem[] {
  const trendDepartmentsMap = new Map(
    (trends?.departments ?? []).map((department) => [department.id, department]),
  );

  return (executiveSummary.departments ?? []).map((department) => {
    const trendDepartment = trendDepartmentsMap.get(department.id);
    const previous =
      trendDepartment?.previous ??
      Math.max(0, department.score - department.variation.value);

    const series: PresentationSparklinePoint[] =
      trendDepartment?.series?.length
        ? mapTrendSeriesToSparklinePoints(trendDepartment.series)
        : [
            {
              period: buildPreviousCompetence(executiveSummary.competence),
              value: previous,
            },
            {
              period: executiveSummary.competence,
              value: department.score,
            },
          ];

    const bestScore =
      trendDepartment?.bestScore ??
      Math.max(...series.map((point) => point.value), department.score);

    const worstScore =
      trendDepartment?.worstScore ??
      Math.min(...series.map((point) => point.value), department.score);

    const netVariation =
      trendDepartment?.netVariation ??
      (series.length >= 2
        ? series[series.length - 1]!.value - series[0]!.value
        : department.variation.value);

    const direction =
      trendDepartment?.direction ?? normalizeDirection(department.trend);

    return {
      id: department.id,
      name: department.name,
      current: department.score,
      previous,
      direction,
      directionLabel: getTrendLabel(direction),
      series,
      netVariation,
      bestScore,
      worstScore,
      currentClassification: trendDepartment?.currentClassification,
      currentContribution:
        trendDepartment?.currentContribution ?? department.contribution,
      lastStepDirection: trendDepartment?.lastStepDirection,
    };
  });
}

function buildDepartmentsOverview(
  departmentsOverview: DepartmentOverviewViewItem[],
): PresentationDepartmentSnapshot[] {
  return departmentsOverview.map((department) => ({
    id: department.id,
    name: department.name,
    shortName: department.shortName,
    score: department.score,
    classification: department.classification,
    contribution: department.contribution,
    weightInIgd: department.weightInIgd,
    strategicSummary: department.strategicSummary,
    variation: {
      value: department.variation.value,
      direction: normalizeDirection(department.variation.direction),
      directionLabel: getTrendLabel(department.variation.direction),
    },
  }));
}

function buildDepartmentFocus(
  departmentId: string | null | undefined,
  departmentDetailsById: Record<string, DepartmentDetailsViewData>,
  indicatorsByDepartmentId: Record<string, IndicatorViewItem[]>,
  trends: TrendsDashboardViewData | null,
): PresentationDepartmentFocus | null {
  if (!departmentId) return null;

  const details = departmentDetailsById[departmentId];
  if (!details) return null;

  const trendDepartment = trends?.departments.find(
    (department) => department.id === departmentId,
  );

  const trendIndicatorsMap = new Map(
    (trends?.indicatorSeriesByDepartmentId?.[departmentId] ?? []).map((item) => [
      item.indicatorId,
      item,
    ]),
  );

  const indicators = details.indicators.map((indicator) => {
    const fallbackIndicator = (indicatorsByDepartmentId[departmentId] ?? []).find(
      (item) => item.id === indicator.id,
    );

    return {
      id: indicator.id,
      name: indicator.name,
      weightPct: indicator.weightPct,
      goalLabel: indicator.goalLabel,
      goalValue: indicator.goalValue,
      goalPeriodicity: getGoalPeriodicityLabel(indicator.goalPeriodicity),
      goalMode: getGoalModeLabel(indicator.goalMode),
      monthlyTargets: (indicator.monthlyTargets ?? []).map((item) => ({
        monthNumber: item.month_number,
        targetValue: item.target_value,
      })),
      strategicDescription:
        indicator.strategicDescription || fallbackIndicator?.name || "",
      scopeType: getScopeTypeLabel(indicator.scopeType),
      performanceDirection: getPerformanceDirectionLabel(
        indicator.performanceDirection,
      ),
      currentValue:
        fallbackIndicator?.value ??
        Object.values(indicator.realized ?? {}).find(
          (value) => value !== null && value !== undefined,
        ) ??
        null,
      realized:
        fallbackIndicator?.realized ??
        indicator.realized ??
        {},
      hasValue:
        indicator.hasValue ??
        fallbackIndicator?.hasValue ??
        fallbackIndicator?.value !== null,
      score: indicator.score,
      gap: indicator.gap,
      gaps: fallbackIndicator?.gaps ?? indicator.gaps ?? {},
      trend: normalizeDirection(indicator.trend),
      trendLabel: getTrendLabel(indicator.trend),
      valueUnit: fallbackIndicator?.valueUnit ?? indicator.valueUnit,
      valuePrefix: fallbackIndicator?.valuePrefix ?? indicator.valuePrefix,
      valueSuffix: fallbackIndicator?.valueSuffix ?? indicator.valueSuffix,
      valueDecimals: fallbackIndicator?.valueDecimals ?? indicator.valueDecimals,
      series: mapIndicatorSeries(trendIndicatorsMap.get(indicator.id)),
    };
  });

  return {
    id: details.id,
    name: details.name,
    shortName: details.shortName,
    weightInIgd: details.weightInIgd,
    score: details.score,
    classification: details.classification,
    contribution: details.contribution,
    aggregationMode: getAggregationModeLabel(details.aggregationMode),
    strategicSummary: details.strategicSummary,
    variation: {
      value: details.variation.value,
      direction: normalizeDirection(details.variation.direction),
      directionLabel: getTrendLabel(details.variation.direction),
    },
    units: details.units.map((unit) => ({
      id: unit.unitId,
      name: unit.unitName,
      score: unit.score,
      hasValue: unit.hasValue,
      classification: unit.classification,
    })),
    indicators,
    series: trendDepartment?.series?.length
      ? mapTrendSeriesToSparklinePoints(trendDepartment.series)
      : undefined,
  };
}

function buildTrendSnapshot(
  trends: TrendsDashboardViewData | null,
): PresentationTrendSnapshot | null {
  if (!trends) return null;

  return {
    competence: trends.competence,
    currentIgd: trends.currentIgd,
    previousIgd: trends.previousIgd,
    currentClassification: trends.currentClassification,
    igdSeries: trends.igdSeries.map((point) => ({
      period: point.period,
      value: point.value,
    })),
    departments: trends.departments.map((department) => ({
      ...department,
      direction: normalizeDirection(department.direction),
      directionLabel: getTrendLabel(department.direction),
      series: mapTrendSeriesToSparklinePoints(department.series),
      netVariation: department.netVariation,
      bestScore: department.bestScore,
      worstScore: department.worstScore,
    })),
    indicatorSeriesByDepartmentId: trends.indicatorSeriesByDepartmentId,
    partialSuccess: trends.partialSuccess,
    errors: trends.errors.map((error) => ({
      competence: error.competence,
      departmentId: error.departmentId,
      source: error.source,
      message: error.message,
    })),
  };
}

function buildAlertSnapshot(
  alerts: AlertsDashboardViewData,
  executiveSummary: ExecutiveDashboardViewData,
): PresentationAlertSnapshot {
  return {
    igdClassification: executiveSummary.classification,
    executive: alerts.executiveAlerts.map((alert) => ({
      ...alert,
      severityLabel: getSeverityLabel(alert.severity),
    })),
    departments: alerts.departmentAlerts.map((alert) => ({
      ...alert,
      severityLabel: getSeverityLabel(alert.severity),
    })),
    indicators: alerts.indicatorAlerts.map((alert) => ({
      ...alert,
      severityLabel: getSeverityLabel(alert.severity),
      goalModeLabel: getGoalModeLabel(alert.goalMode),
      performanceDirectionLabel: getPerformanceDirectionLabel(
        alert.performanceDirection,
      ),
    })),
    partialSuccess: alerts.partialSuccess,
    errors: alerts.errors.map((error) => ({
      departmentId: error.departmentId,
      source: error.source,
      message: error.message,
    })),
  };
}

type BuildPresentationViewDataParams = {
  executiveSummary: ExecutiveDashboardViewData;
  executiveAlerts: ExecutiveAlertViewItem[];
  alerts: AlertsDashboardViewData;
  departmentsOverview: DepartmentOverviewViewItem[];
  departmentDetailsById: Record<string, DepartmentDetailsViewData>;
  indicatorsByDepartmentId: Record<string, IndicatorViewItem[]>;
  trends: TrendsDashboardViewData | null;
  focusDepartmentId?: string | null;
};

export function buildPresentationViewData({
  executiveSummary,
  executiveAlerts,
  alerts,
  departmentsOverview,
  departmentDetailsById,
  indicatorsByDepartmentId,
  trends,
  focusDepartmentId,
}: BuildPresentationViewDataParams): PresentationViewData {
  const departments = buildDepartmentBoard(executiveSummary, trends);
  const departmentsOverviewSnapshot = buildDepartmentsOverview(departmentsOverview);
  const departmentFocus = buildDepartmentFocus(
    focusDepartmentId,
    departmentDetailsById,
    indicatorsByDepartmentId,
    trends,
  );
  const trend = buildTrendSnapshot(trends);
  const alertSnapshot = buildAlertSnapshot(alerts, executiveSummary);
  const variationDirection = normalizeDirection(executiveSummary.variation.direction);
  const sortedDepartments = [...executiveSummary.departments].sort(
    (a, b) => b.score - a.score,
  );
  const topDepartment = sortedDepartments[0]?.name ?? "—";
  const topRisk =
    [...executiveSummary.departments].sort((a, b) => a.score - b.score)[0]?.name ??
    "—";

  return {
    competence: executiveSummary.competence,
    igd: executiveSummary.igd,
    igdExact: executiveSummary.igdExact,
    classification: executiveSummary.classification,
    trendLabel: getPresentationTrendLabel(variationDirection),
    currentIgd: executiveSummary.igd,
    previousIgd: trends?.previousIgd ?? executiveSummary.igd,
    variationValue: executiveSummary.variation.value,
    variationDirection,
    variationDirectionLabel: getTrendLabel(variationDirection),
    topDepartment,
    topRisk,
    currentPeriod: executiveSummary.competence,
    previousPeriod: buildPreviousCompetence(executiveSummary.competence),
    departments,
    executiveAlerts,
    kpis: buildExecutiveKpis(executiveSummary, trends),
    departmentsOverview: departmentsOverviewSnapshot,
    departmentFocus,
    trend,
    alerts: alertSnapshot,
  };
}