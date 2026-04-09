import type { ExecutiveAlertViewItem } from "./alerts";
import type { ExecutiveDashboardViewData } from "./executiveSummary";

export type PresentationDepartmentBoardItem = {
  id: string;
  name: string;
  current: number;
  previous: number;
  direction: "up" | "down" | "stable";
};

export type PresentationViewData = {
  competence: string;
  igd: number;
  classification: string;
  trendLabel: string;
  currentIgd: number;
  previousIgd: number;
  variationValue: number;
  variationDirection: "up" | "down" | "stable";
  topDepartment: string;
  topRisk: string;
  currentPeriod: string;
  previousPeriod: string;
  departments: PresentationDepartmentBoardItem[];
  executiveAlerts: ExecutiveAlertViewItem[];
};

function getDirectionFromVariation(
  value: number,
): "up" | "down" | "stable" {
  if (value > 0.09) return "up";
  if (value < -0.09) return "down";
  return "stable";
}

function getTrendLabel(direction: "up" | "down" | "stable"): string {
  if (direction === "up") return "Melhora no período";
  if (direction === "down") return "Queda no período";
  return "Estabilidade no período";
}

function buildPreviousCompetence(competence: string): string {
  const [yearStr, monthStr] = competence.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);

  if (month === 1) {
    return `${year - 1}-12`;
  }

  return `${year}-${String(month - 1).padStart(2, "0")}`;
}

export function buildPresentationViewData(params: {
  executiveSummary: ExecutiveDashboardViewData;
  executiveAlerts: ExecutiveAlertViewItem[];
}): PresentationViewData {
  const { executiveSummary, executiveAlerts } = params;

  const departmentsSorted = [...executiveSummary.departments].sort(
    (a, b) => b.score - a.score,
  );
  const bestDepartment = departmentsSorted[0];
  const topRiskAlert = executiveAlerts[0] ?? null;

  const variationValue = executiveSummary.variation.value;
  const variationDirection = getDirectionFromVariation(variationValue);
  const trendLabel = getTrendLabel(variationDirection);

  const previousIgd = Math.max(0, executiveSummary.igd - variationValue);

  const departments = executiveSummary.departments.map((department) => {
    const previous = Math.max(0, department.score - department.variation.value);

    return {
      id: department.id,
      name: department.name,
      current: department.score,
      previous,
      direction: department.variation.direction,
    };
  });

  return {
    competence: executiveSummary.competence,
    igd: executiveSummary.igd,
    classification: executiveSummary.classification,
    trendLabel,
    currentIgd: executiveSummary.igd,
    previousIgd,
    variationValue,
    variationDirection,
    topDepartment: bestDepartment?.name ?? "—",
    topRisk: topRiskAlert?.title ?? "—",
    currentPeriod: executiveSummary.competence,
    previousPeriod: buildPreviousCompetence(executiveSummary.competence),
    departments,
    executiveAlerts,
  };
}