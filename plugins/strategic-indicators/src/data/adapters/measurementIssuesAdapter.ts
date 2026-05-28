import type {
  StrategicIndicatorsAlertSummaryApi,
  StrategicIndicatorsMeasurementIssueApi,
} from "../types/departmentTreeBundle";
import type {
  DepartmentTreeAlertSummary,
  DepartmentTreeMeasurementIssue,
} from "../types/departmentTree";

export function adaptMeasurementIssuesToView(
  errors: StrategicIndicatorsMeasurementIssueApi[] | undefined,
): DepartmentTreeMeasurementIssue[] {
  if (!errors?.length) {
    return [];
  }

  return errors.map((item) => ({
    departmentId: String(item.department_id ?? "geral"),
    source: String(item.source ?? "desconhecida"),
    message: String(item.message ?? "Falha na coleta."),
    code: item.code ? String(item.code) : undefined,
  }));
}

export function adaptAlertsSummaryToView(
  alerts: StrategicIndicatorsAlertSummaryApi[] | undefined,
): DepartmentTreeAlertSummary[] {
  if (!alerts?.length) {
    return [];
  }

  return alerts.map((item) => ({
    title: item.title,
    severity: item.severity,
    impact: item.impact,
    recommendation: item.recommendation,
  }));
}

export function buildMeasurementIssuesDescription(
  errors: DepartmentTreeMeasurementIssue[],
): string {
  return errors
    .map(
      (item) =>
        `• ${item.departmentId}: ${item.message}${
          item.source ? ` [fonte: ${item.source}]` : ""
        }`,
    )
    .join("\n");
}
