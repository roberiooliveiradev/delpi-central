import {
  fetchAudit,
  fetchNonconformities,
  type AuditDetail,
  type Nonconformity,
} from "../api/audit5sApi";
import {
  auditStatusLabel,
  canAccessNc,
  ncPriorityLabel,
  ncStatusLabel,
  sensoName,
  shiftLabel,
} from "../constants/audit5s";
import { formatAuditDate } from "./auditList";
import { getScoreSummaryLabel } from "./scoreLabels";
import type { ExportDocument } from "./exportDocument";
import { formatPersonName } from "./formatPersonName";

export type AuditExportData = {
  detail: AuditDetail;
  nonconformities?: Nonconformity[];
};

function formatCriterionScore(
  score: number | null | undefined,
  isNotApplicable: boolean,
): string {
  if (isNotApplicable) return "N/A";
  if (score == null) return "—";
  const label = getScoreSummaryLabel(score, false);
  return label ? `${score} — ${label}` : String(score);
}

function sortCriteria(detail: AuditDetail) {
  return [...detail.criteria].sort((left, right) => {
    if (left.senso_order !== right.senso_order) {
      return left.senso_order - right.senso_order;
    }
    return left.sort_order - right.sort_order;
  });
}

export function buildAuditExportDocument(data: AuditExportData): ExportDocument {
  const { detail, nonconformities = [] } = data;
  const branch = detail.branch_code === "01" || detail.branch_code === "02" ? detail.branch_code : null;
  const overallScore = detail.scores.overall_percentual ?? detail.overall_score_pct;
  const auditorNames = detail.auditors
    .map((item) => formatPersonName(item.display_name))
    .filter(Boolean)
    .join(", ");

  const headerRows: [string, string][] = [
    ["Código", detail.audit_code],
    ["Data", formatAuditDate(detail.audit_date)],
    ["Área", detail.area_name],
    ["Responsável", formatPersonName(detail.area_responsible) || detail.area_responsible || "—"],
    ["Filial", detail.branch_code],
    ["Turno", shiftLabel(detail.shift)],
    ["Status", auditStatusLabel(detail.status, overallScore)],
    ["Auditores", auditorNames || "—"],
    ["% Geral", overallScore != null ? `${overallScore}%` : "—"],
    [
      "Progresso",
      `${detail.progress.scored} de ${detail.progress.total} critérios (${detail.progress.pending} pendentes)`,
    ],
  ];

  const sensoRows = [...detail.scores.sensos]
    .sort((left, right) => left.senso_order - right.senso_order)
    .map(
      (item) =>
        [
          `Senso ${item.senso_order} — ${sensoName(item.senso_order, undefined, branch)}`,
          item.percentual != null ? `${item.percentual}%` : "—",
        ] as [string, string],
    );

  const responseByCriterion = new Map(
    detail.responses.map((response) => [response.criterion_id, response]),
  );

  const criteriaRows = sortCriteria(detail).map((criterion) => {
    const response = responseByCriterion.get(criterion.id);
    return [
      String(criterion.senso_order),
      sensoName(criterion.senso_order, criterion.senso_name, branch),
      criterion.code,
      criterion.description,
      formatCriterionScore(response?.score, Boolean(response?.is_not_applicable)),
      response?.observation?.trim() || "—",
    ];
  });

  const ncRows = nonconformities.map((item) => [
    item.criterion_code,
    item.description,
    ncStatusLabel(item.status),
    ncPriorityLabel(item.priority),
    item.responsible_name,
    formatAuditDate(item.due_date),
    item.root_cause?.trim() || "—",
    item.corrective_action?.trim() || "—",
  ]);

  const tableSections = [
    {
      title: "Critérios avaliados",
      headers: ["Senso", "Nome do senso", "Código", "Critério", "Nota", "Observação"],
      rows: criteriaRows,
    },
    ...(ncRows.length
      ? [
          {
            title: "Não conformidades",
            headers: [
              "Critério",
              "Descrição",
              "Status",
              "Prioridade",
              "Responsável",
              "Prazo",
              "Causa raiz",
              "Ação corretiva",
            ],
            rows: ncRows,
          },
        ]
      : []),
  ];

  return {
    title: `Auditoria 5S — ${detail.audit_code}`,
    fieldSections: [
      { title: "Cabeçalho", rows: headerRows },
      ...(sensoRows.length ? [{ title: "Notas por senso", rows: sensoRows }] : []),
    ],
    tableSections,
  };
}

export async function loadAuditExportData(auditId: string): Promise<AuditExportData> {
  const detail = await fetchAudit(auditId);
  const nonconformities = canAccessNc(detail.status)
    ? await fetchNonconformities(auditId)
    : undefined;

  return { detail, nonconformities };
}

function buildExportFilename(auditCode: string, extension: "xlsx" | "pdf"): string {
  const safeCode = auditCode.replace(/[^\w.-]+/g, "_");
  return `auditoria-5s_${safeCode}.${extension}`;
}

export async function exportAuditExcel(data: AuditExportData): Promise<void> {
  const { exportDocumentExcel } = await import("./exportDocument");
  const document = buildAuditExportDocument(data);
  await exportDocumentExcel(document, buildExportFilename(data.detail.audit_code, "xlsx"));
}

export async function exportAuditPdf(data: AuditExportData): Promise<void> {
  const { exportDocumentPdf, sanitizeFilename } = await import("./exportDocument");
  const document = buildAuditExportDocument(data);
  await exportDocumentPdf(document, sanitizeFilename(document.title));
}
