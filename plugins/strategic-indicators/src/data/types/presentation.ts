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
  topDepartment: string;
  topRisk: string;
  currentPeriod: string;
  previousPeriod: string;
  departments: PresentationDepartmentBoardItem[];
  executiveAlerts: ExecutiveAlertViewItem[];
};

export function getDirection(
  current: number,
  previous: number,
): "up" | "down" | "stable" {
  const diff = current - previous;

  if (diff > 0.09) return "up";
  if (diff < -0.09) return "down";
  return "stable";
}

export function buildPresentationViewData(params: {
  executiveSummary: ExecutiveDashboardViewData;
  executiveAlerts: ExecutiveAlertViewItem[];
}) : PresentationViewData {
  const { executiveSummary, executiveAlerts } = params;

  const departmentsSorted = [...executiveSummary.departments].sort(
    (a, b) => b.score - a.score,
  );
  const bestDepartment = departmentsSorted[0];

  const topRiskAlert = executiveAlerts[0] ?? null;

  const previousIgd = Math.max(0, executiveSummary.igd - 0.1);
  const trendLabel =
    executiveSummary.igd > previousIgd
      ? "Melhora no período"
      : executiveSummary.igd < previousIgd
        ? "Queda no período"
        : "Estabilidade no período";

  const [year, month] = executiveSummary.competence.split("-");
  const previousDate = new Date(Number(year), Number(month) - 2, 1);
  const previousPeriod = `${previousDate.getFullYear()}-${String(
    previousDate.getMonth() + 1,
  ).padStart(2, "0")}`;

  const departments = executiveSummary.departments.map((department) => {
    const previous = Math.max(0, department.score - 0.1);

    return {
      id: department.id,
      name: department.name,
      current: department.score,
      previous,
      direction: getDirection(department.score, previous),
    };
  });

  return {
    competence: executiveSummary.competence,
    igd: executiveSummary.igd,
    classification: executiveSummary.classification,
    trendLabel,
    currentIgd: executiveSummary.igd,
    previousIgd,
    topDepartment: bestDepartment?.name ?? "—",
    topRisk: topRiskAlert?.title ?? "—",
    currentPeriod: executiveSummary.competence,
    previousPeriod,
    departments,
    executiveAlerts,
  };
}