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
  unit: string | null;
  paProductCode: string | null;
  paProductDescription: string | null;

  toolSnapshot: string | null;
  resource: string | null;

  plannedQty: number | null;
  pendingQty: number | null;
  operationPendingQty: number | null;

  scheduledDate: string | null;
  scheduledStartTime: string | null;
  scheduledEndDate: string | null;
  scheduledEndTime: string | null;
  dueDate: string | null;

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
    unit: text(operation.unit),
    paProductCode: text(operation.paProductCode),
    paProductDescription: text(operation.paProductDescription),

    toolSnapshot: text(operation.toolSnapshot),
    resource: text(operation.resource),

    plannedQty: num(operation.plannedQty),
    pendingQty: num(operation.pendingQty),
    operationPendingQty: num(operation.operationPendingQty),

    scheduledDate: text(operation.scheduledDate),
    scheduledStartTime: text(operation.scheduledStartTime),
    scheduledEndDate: text(operation.scheduledEndDate),
    scheduledEndTime: text(operation.scheduledEndTime),
    dueDate: text(operation.dueDate),

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

/** `YYYY-MM-DD` → `dd/mm/aaaa` sem deslocamento de fuso. */
export function formatProcessIssueDate(
  value: string | null | undefined,
): string | null {
  const raw = (value ?? "").trim();
  if (!raw) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(raw);
  if (match) return `${match[3]}/${match[2]}/${match[1]}`;
  return raw;
}

/** `HH:MM[:SS]` → `HH:MM`. */
export function formatProcessIssueTime(
  value: string | null | undefined,
): string | null {
  const raw = (value ?? "").trim();
  if (!raw) return null;
  const match = /^(\d{2}):(\d{2})/.exec(raw);
  return match ? `${match[1]}:${match[2]}` : raw;
}

/** Combina data + hora do snapshot (ex.: `12/03/2026 · 07:30`). */
export function formatProcessIssueSchedule(
  date: string | null | undefined,
  time: string | null | undefined,
): string | null {
  const day = formatProcessIssueDate(date);
  const hour = formatProcessIssueTime(time);
  if (day && hour) return `${day} · ${hour}`;
  return day ?? hour;
}
