import type { StrategicIndicatorsErrorContext } from "../errors/strategicIndicatorsError";
import type { StrategicIndicatorsErrorView } from "../errors/strategicIndicatorsError";
import type {
  StrategicIndicatorsAlertSummaryApi,
  StrategicIndicatorsMeasurementIssueApi,
  MeasurementVersionsMetaApi,
} from "../types/departmentTreeBundle";
import type {
  DepartmentTreeAlertSummary,
  DepartmentTreeDataQuality,
  DepartmentTreeMeasurementIssue,
  DepartmentTreeSnapshotVersions,
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

const DEPARTMENT_LABELS: Record<string, string> = {
  engineering: "Engenharia",
  production: "Produção",
  commercial: "Comercial",
  quality: "Qualidade",
  hr: "RH",
  financial: "Financeiro",
  supplies: "Suprimentos",
};

function departmentLabel(departmentId: string) {
  return DEPARTMENT_LABELS[departmentId] ?? departmentId;
}

export function adaptMeasurementVersionsMeta(
  meta: MeasurementVersionsMetaApi | null | undefined,
): DepartmentTreeSnapshotVersions | undefined {
  if (!meta) {
    return undefined;
  }

  return {
    servingVersion: meta.serving_version,
    latestVersion: meta.latest_version,
    versionCount: meta.version_count,
    servingFallbackFromPreviousClean: meta.serving_fallback_from_previous_clean,
    isClean: meta.is_clean,
  };
}

export function buildDataQualityErrorView(
  dataQuality: DepartmentTreeDataQuality,
  context: StrategicIndicatorsErrorContext,
): StrategicIndicatorsErrorView {
  const issueLines = buildMeasurementIssuesDescription(dataQuality.errors);
  const alertLines = dataQuality.alertsSummary
    .map(
      (alert) =>
        `• ${alert.title} (${alert.severity}): ${alert.impact}${
          alert.recommendation ? ` — ${alert.recommendation}` : ""
        }`,
    )
    .join("\n");

  const failedDepartments = [
    ...new Set(dataQuality.errors.map((item) => item.departmentId)),
  ];

  const causes = failedDepartments.map(
    (departmentId) =>
      `${departmentLabel(departmentId)}: medição indisponível neste período (nota pode aparecer como 0,0).`,
  );

  if (dataQuality.alertsSummary.length) {
    causes.push(
      "O cálculo consolidado do IGD diverge do esperado por falhas em uma ou mais fontes.",
    );
  }

  return {
    title: "Coleta incompleta — leitura do período pode estar incorreta",
    summary:
      "Parte das integrações não respondeu. Revise as fontes com falha antes de usar o painel como fechamento do período.",
    context,
    causes,
    suggestions: [
      "Confirme se api-delpi e as demais integrações estão disponíveis para a competência selecionada.",
      'Use "Atualizar" após corrigir as fontes.',
      "Abra o detalhe técnico para ver departamento, mensagem e origem de cada falha.",
    ],
    technicalDetail: [alertLines, issueLines].filter(Boolean).join("\n\n"),
    rawMessage: issueLines,
  };
}
