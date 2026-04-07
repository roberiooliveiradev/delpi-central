import type {
  DepartmentOverviewViewItem,
  StrategicIndicatorsDepartmentsResponse,
} from "../types/departments";

export function adaptDepartmentsToView(
  response: StrategicIndicatorsDepartmentsResponse,
): DepartmentOverviewViewItem[] {
  return response.items.map((item) => ({
    id: item.id,
    name: item.name,
    shortName: item.short_name,
    weightInIgd: item.weight_pct,
    score: item.score,
    classification: item.classification,
    strategicSummary: item.strategic_summary,
  }));
}