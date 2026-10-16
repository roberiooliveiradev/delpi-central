/**
 * Parser/view-model do snapshot persistido no payload do `process-issue` (P4).
 *
 * O payload é um snapshot histórico escrito pelo Production Control na P2 —
 * a tela apenas interpreta o que foi registrado. Campos ausentes ou com
 * formato inesperado nunca quebram a renderização (viram `null`/`[]`).
 */

export const PROCESS_ISSUE_TYPE_CODE = "process-issue";

/** Labels canônicos dos motivos — espelho de `process_issue_catalog.py`. */
export const PROCESS_ISSUE_LABELS: Readonly<Record<string, string>> = {
  work_center_incompatible: "CT / posto não adequado",
  machine_limitation: "Limitação da máquina ou bancada",
  tool_not_linked: "Ferramenta não informada ou não vinculada",
  material_not_linked: "Matéria-prima não vinculada à operação",
  process_information_missing: "Informação de processo incompleta",
  other: "Outro problema de processo",
};

const ISSUE_LABEL_FALLBACK = "Problema de processo";

export function processIssueLabel(
  code: string | null | undefined,
): string {
  const normalized = (code ?? "").trim();
  return PROCESS_ISSUE_LABELS[normalized] ?? ISSUE_LABEL_FALLBACK;
}

export type ProcessIssueMaterial = {
  productCode: string | null;
  description: string | null;
  unit: string | null;
  originalQty: number | null;
  openQty: number | null;
  consumedQty: number | null;
};

export type ProcessIssuePayloadView = {
  source: string | null;
  reportedAt: string | null;

  issueCode: string | null;
  issueLabel: string;
  reportedToolCode: string | null;
  reportedMaterialCode: string | null;
  note: string | null;

  operatorCode: string | null;
  operatorName: string | null;

  productionOrder: string | null;
  operationCode: string | null;
  operationDescription: string | null;
  reportedWorkCenter: string | null;
  workCenterName: string | null;

  productCode: string | null;
  productDescription: string | null;
  paProductCode: string | null;
  paProductDescription: string | null;

  toolSnapshot: string | null;
  resource: string | null;

  materialsSnapshotAvailable: boolean;
  materials: ProcessIssueMaterial[];
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function text(value: unknown): string | null {
  const raw = typeof value === "string" ? value : value == null ? "" : String(value);
  const trimmed = raw.trim();
  return trimmed || null;
}

function num(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  const parsed = typeof value === "string" ? Number(value) : Number.NaN;
  return Number.isFinite(parsed) ? parsed : null;
}

function toMaterial(raw: unknown): ProcessIssueMaterial {
  const row = asRecord(raw);
  return {
    productCode: text(row.productCode),
    description: text(row.description),
    unit: text(row.unit),
    originalQty: num(row.originalQty),
    openQty: num(row.openQty),
    consumedQty: num(row.consumedQty),
  };
}

export function parseProcessIssuePayload(
  payload: unknown,
): ProcessIssuePayloadView {
  const root = asRecord(payload);
  const issue = asRecord(root.issue);
  const operator = asRecord(root.operator);
  const operation = asRecord(root.operation);
  const issueCode = text(issue.code);

  const rawMaterials = Array.isArray(root.materials) ? root.materials : [];

  return {
    source: text(root.source),
    reportedAt: text(root.reportedAt),

    issueCode,
    issueLabel: processIssueLabel(issueCode),
    reportedToolCode: text(issue.reportedToolCode),
    reportedMaterialCode: text(issue.reportedMaterialCode),
    note: text(issue.note),

    operatorCode: text(operator.code),
    operatorName: text(operator.name),

    productionOrder: text(operation.productionOrder),
    operationCode: text(operation.operationCode),
    operationDescription: text(operation.description),
    reportedWorkCenter: text(operation.reportedWorkCenter),
    workCenterName: text(operation.workCenterName),

    productCode: text(operation.productCode),
    productDescription: text(operation.productDescription),
    paProductCode: text(operation.paProductCode),
    paProductDescription: text(operation.paProductDescription),

    toolSnapshot: text(operation.toolSnapshot),
    resource: text(operation.resource),

    materialsSnapshotAvailable: root.materialsSnapshotAvailable === true,
    materials: rawMaterials.map(toMaterial),
  };
}

const qtyFormatter = new Intl.NumberFormat("pt-BR", {
  maximumFractionDigits: 4,
});

export function formatProcessIssueQty(
  value: number | null | undefined,
): string | null {
  return value == null ? null : qtyFormatter.format(value);
}
