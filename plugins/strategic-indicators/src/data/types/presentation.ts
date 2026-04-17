import type {
  AlertsDashboardViewData,
  DepartmentAlertViewItem,
  ExecutiveAlertViewItem,
  IndicatorAlertViewItem,
} from "./alerts";
import type {
  DepartmentDetailsViewData,
  DepartmentIndicator,
  DepartmentUnit,
} from "./departmentDetails";
import type { DepartmentOverviewViewItem } from "./departments";
import type { ExecutiveDashboardViewData } from "./executiveSummary";
import type { IndicatorViewItem } from "./indicators";
import type { TrendsDashboardViewData } from "./trends";
import {
  getAggregationModeLabel,
  getGoalModeLabel,
  getGoalPeriodicityLabel,
  getPerformanceDirectionLabel,
  getScopeTypeLabel,
  getSeverityLabel,
  getTrendLabel,
} from "../../ui/presentation/labels";

export type PresentationDepartmentBoardItem = {
  id: string;
  name: string;
  current: number;
  previous: number;
  direction: "up" | "down" | "stable";
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
  strategicDescription: string;
  scopeType: string;
  performanceDirection: string;
  currentValue: number;
  score: number;
  gap: number;
  trend: "up" | "down" | "stable";
  trendLabel: string;
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
    score: number;
    classification: string;
  }>;
  indicators: PresentationDepartmentIndicatorSnapshot[];
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
  departments: Array<{
    id: string;
    name: string;
    current: number;
    previous: number;
    direction: "up" | "down" | "stable";
    directionLabel: string;
  }>;
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

function getDirectionFromVariation(
  value: number,
): "up" | "down" | "stable" {
  if (value > 0.09) return "up";
  if (value < -0.09) return "down";
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

function formatNumber(value: number, fractionDigits = 1): string {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

function getIndicatorCurrentValue(
  indicator: DepartmentIndicator,
  fallbackIndicator?: IndicatorViewItem,
): number {
  const realizedValues = Object.values(indicator.realized ?? {}).filter(
    (value) => Number.isFinite(value),
  );

  if (realizedValues.length > 0) {
    return realizedValues[realizedValues.length - 1] ?? 0;
  }

  return fallbackIndicator?.value ?? 0;
}

function buildDepartmentBoardItems(
  executiveSummary: ExecutiveDashboardViewData,
): PresentationDepartmentBoardItem[] {
  return executiveSummary.departments.map((department) => {
    const previous = Math.max(0, department.score - department.variation.value);

    return {
      id: department.id,
      name: department.name,
      current: department.score,
      previous,
      direction: normalizeDirection(department.variation.direction),
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
    contribution: 0,
    weightInIgd: department.weightInIgd,
    strategicSummary: department.strategicSummary,
    variation: {
      value: department.variation.value,
      direction: normalizeDirection(department.variation.direction),
      directionLabel: getTrendLabel(department.variation.direction),
    },
  }));
}

function buildDepartmentFocus(params: {
  departmentId?: string | null;
  departmentDetailsById?: Record<string, DepartmentDetailsViewData>;
  indicatorsByDepartmentId?: Record<string, IndicatorViewItem[]>;
}): PresentationDepartmentFocus | null {
  const {
    departmentId,
    departmentDetailsById = {},
    indicatorsByDepartmentId = {},
  } = params;

  if (!departmentId) {
    return null;
  }

  const details = departmentDetailsById[departmentId];

  if (!details) {
    return null;
  }

  const indicators = indicatorsByDepartmentId[departmentId] ?? [];
  const indicatorsById = new Map(indicators.map((item) => [item.id, item]));

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
    units: details.units.map((unit: DepartmentUnit) => ({
      id: unit.unitId,
      name: unit.unitName,
      score: unit.score,
      classification: unit.classification,
    })),
    indicators: details.indicators.map((indicator: DepartmentIndicator) => {
      const fallbackIndicator = indicatorsById.get(indicator.id);
      const currentValue = getIndicatorCurrentValue(indicator, fallbackIndicator);

      return {
        id: indicator.id,
        name: indicator.name,
        weightPct: indicator.weightPct,
        goalLabel: indicator.goalLabel,
        goalValue: indicator.goalValue,
        goalPeriodicity: getGoalPeriodicityLabel(indicator.goalPeriodicity),
        goalMode: getGoalModeLabel(indicator.goalMode),
        strategicDescription: indicator.strategicDescription,
        scopeType: getScopeTypeLabel(indicator.scopeType),
        performanceDirection: getPerformanceDirectionLabel(
          indicator.performanceDirection,
        ),
        currentValue,
        score: indicator.score,
        gap: indicator.gap,
        trend: normalizeDirection(indicator.trend),
        trendLabel: getTrendLabel(indicator.trend),
      };
    }),
  };
}

function buildTrendSnapshot(
  trends: TrendsDashboardViewData | null | undefined,
): PresentationTrendSnapshot | null {
  if (!trends) {
    return null;
  }

  return {
    competence: trends.competence,
    currentIgd: trends.currentIgd,
    previousIgd: trends.previousIgd,
    currentClassification: trends.currentClassification,
    igdSeries: trends.igdSeries.map((item) => ({
      period: item.period,
      value: item.value,
    })),
    departments: trends.departments.map((department) => ({
      id: department.id,
      name: department.name,
      current: department.current,
      previous: department.previous,
      direction: normalizeDirection(department.direction),
      directionLabel: getTrendLabel(department.direction),
    })),
    partialSuccess: trends.partialSuccess,
    errors: trends.errors.map((error) => ({
      competence: error.competence,
      departmentId: error.departmentId,
      source: error.source,
      message: error.message,
    })),
  };
}

function buildAlertsSnapshot(
  alerts: AlertsDashboardViewData,
): PresentationAlertSnapshot {
  return {
    igdClassification: alerts.igdClassification,
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

function buildKpis(params: {
  executiveSummary: ExecutiveDashboardViewData;
  topDepartment: string;
  topRisk: string;
  trendLabel: string;
}): PresentationKpiCard[] {
  const { executiveSummary, topDepartment, topRisk, trendLabel } = params;

  return [
    {
      id: "igd-atual",
      label: "IGD atual",
      value: formatNumber(executiveSummary.igd),
      support: executiveSummary.classification,
    },
    {
      id: "variacao",
      label: "Variação",
      value: `${executiveSummary.variation.value > 0 ? "+" : ""}${formatNumber(
        executiveSummary.variation.value,
      )}`,
      support: executiveSummary.variation.vsLabel,
    },
    {
      id: "tendencia",
      label: "Tendência",
      value: trendLabel,
      support: "Comparação com o período anterior",
    },
    {
      id: "melhor-area",
      label: "Área destaque",
      value: topDepartment,
      support: "Melhor score no período",
    },
    {
      id: "risco-prioritario",
      label: "Risco prioritário",
      value: topRisk,
      support: "Principal alerta executivo",
    },
  ];
}

export function buildPresentationViewData(params: {
  executiveSummary: ExecutiveDashboardViewData;
  executiveAlerts: ExecutiveAlertViewItem[];
  alerts?: AlertsDashboardViewData;
  departmentsOverview?: DepartmentOverviewViewItem[];
  departmentDetailsById?: Record<string, DepartmentDetailsViewData>;
  indicatorsByDepartmentId?: Record<string, IndicatorViewItem[]>;
  trends?: TrendsDashboardViewData | null;
  focusDepartmentId?: string | null;
}): PresentationViewData {
  const {
    executiveSummary,
    executiveAlerts,
    alerts,
    departmentsOverview = [],
    departmentDetailsById = {},
    indicatorsByDepartmentId = {},
    trends = null,
    focusDepartmentId,
  } = params;

  const departmentsSorted = [...executiveSummary.departments].sort(
    (a, b) => b.score - a.score,
  );
  const bestDepartment = departmentsSorted[0];
  const topRiskAlert = executiveAlerts[0] ?? null;

  const variationValue = executiveSummary.variation.value;
  const variationDirection = getDirectionFromVariation(variationValue);
  const variationDirectionLabel = getTrendLabel(variationDirection);
  const trendLabel = getPresentationTrendLabel(variationDirection);
  const previousIgd = Math.max(0, executiveSummary.igd - variationValue);
  const departments = buildDepartmentBoardItems(executiveSummary);

  const overview =
    departmentsOverview.length > 0
      ? buildDepartmentsOverview(departmentsOverview)
      : executiveSummary.departments.map((department) => ({
          id: department.id,
          name: department.name,
          shortName: department.shortName,
          score: department.score,
          classification: "",
          contribution: department.contribution,
          weightInIgd: department.weightPct,
          strategicSummary: department.strategicSummary,
          variation: {
            value: department.variation.value,
            direction: normalizeDirection(department.variation.direction),
            directionLabel: getTrendLabel(department.variation.direction),
          },
        }));

  const effectiveFocusDepartmentId =
    focusDepartmentId ??
    overview[0]?.id ??
    executiveSummary.departments[0]?.id ??
    null;

  const departmentFocus = buildDepartmentFocus({
    departmentId: effectiveFocusDepartmentId,
    departmentDetailsById,
    indicatorsByDepartmentId,
  });

  const alertsSnapshot = buildAlertsSnapshot(
    alerts ?? {
      competence: executiveSummary.competence,
      igdClassification: executiveSummary.classification,
      executiveAlerts,
      departmentAlerts: [],
      indicatorAlerts: [],
      partialSuccess: false,
      errors: [],
    },
  );

  return {
    competence: executiveSummary.competence,
    igd: executiveSummary.igd,
    igdExact: executiveSummary.igdExact,
    classification: executiveSummary.classification,
    trendLabel,
    currentIgd: executiveSummary.igd,
    previousIgd,
    variationValue,
    variationDirection,
    variationDirectionLabel,
    topDepartment: bestDepartment?.name ?? "—",
    topRisk: topRiskAlert?.title ?? "—",
    currentPeriod: executiveSummary.competence,
    previousPeriod: buildPreviousCompetence(executiveSummary.competence),
    departments,
    executiveAlerts,
    kpis: buildKpis({
      executiveSummary,
      topDepartment: bestDepartment?.name ?? "—",
      topRisk: topRiskAlert?.title ?? "—",
      trendLabel,
    }),
    departmentsOverview: overview,
    departmentFocus,
    trend: buildTrendSnapshot(trends),
    alerts: alertsSnapshot,
  };
}