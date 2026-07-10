import type { NcCandidate, Nonconformity, ResponseAttachment } from "../api/audit5sApi";
import type { NcAttachmentMap } from "../api/audit5sApi";
import { hasNcEvidence } from "./ncAttachments";

export type NcFormState = {
  description: string;
  root_cause: string;
  corrective_action: string;
  responsible_name: string;
  due_date: string;
  priority: "" | "high" | "medium" | "low";
};

export type NcTreatmentItem = {
  criterionId: string;
  responseId: string;
  code: string;
  criterionDescription: string;
  sensoOrder: number;
  sensoName: string;
  score: number;
  observation: string | null;
  evaluationAttachment: ResponseAttachment | null;
  nc: Nonconformity | null;
};

export type NcTreatmentStats = {
  total: number;
  registered: number;
  inTreatment: number;
  finalized: number;
  pending: number;
  progressPct: number;
};

export function defaultDueDate(): string {
  return new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
}

export function emptyNcForm(): NcFormState {
  return {
    description: "",
    root_cause: "",
    corrective_action: "",
    responsible_name: "",
    due_date: defaultDueDate(),
    priority: "",
  };
}

export function formFromNonconformity(nc: Nonconformity): NcFormState {
  return {
    description: nc.description ?? "",
    root_cause: nc.root_cause ?? "",
    corrective_action: nc.corrective_action ?? "",
    responsible_name: nc.responsible_name ?? "",
    due_date: nc.due_date ?? defaultDueDate(),
    priority: nc.priority ?? "",
  };
}

export function buildNcTreatmentItems(
  candidates: NcCandidate[],
  ncs: Nonconformity[],
): NcTreatmentItem[] {
  const ncByResponse = new Map(ncs.map((nc) => [nc.response_id, nc]));

  return candidates.map((item) => ({
    criterionId: item.id,
    responseId: item.response.id,
    code: item.code,
    criterionDescription: item.description,
    sensoOrder: item.senso_order,
    sensoName: item.senso_name,
    score: item.response.score ?? 0,
    observation: item.response.observation,
    evaluationAttachment: item.response.attachment ?? null,
    nc: ncByResponse.get(item.response.id) ?? null,
  }));
}

export function isNcPlanComplete(form: NcFormState): boolean {
  return (
    form.description.trim().length >= 3 &&
    form.responsible_name.trim().length >= 2 &&
    Boolean(form.due_date) &&
    form.root_cause.trim().length >= 3 &&
    form.corrective_action.trim().length >= 3
  );
}

export function canCreateNc(form: NcFormState): boolean {
  return (
    form.description.trim().length >= 3 &&
    form.responsible_name.trim().length >= 2 &&
    Boolean(form.due_date)
  );
}

export function isNcFinalized(nc: Nonconformity | null | undefined): boolean {
  return nc?.status === "closed";
}

export function canFinalizeNcAction(
  form: NcFormState,
  nc: Nonconformity | null | undefined,
  attachmentsByNcId: NcAttachmentMap,
): boolean {
  if (!nc || isNcFinalized(nc)) return false;
  if (!isNcPlanComplete(form)) return false;
  const evidence = hasNcEvidence(nc.id, attachmentsByNcId);
  return evidence.before && evidence.after;
}

export function computeNcTreatmentStats(
  items: NcTreatmentItem[],
  forms: Record<string, NcFormState>,
): NcTreatmentStats {
  const total = items.length;
  let registered = 0;
  let inTreatment = 0;
  let finalized = 0;

  for (const item of items) {
    if (!item.nc) continue;
    registered += 1;
    if (item.nc.status === "closed") {
      finalized += 1;
      continue;
    }
    const form = forms[item.responseId] ?? formFromNonconformity(item.nc);
    if (isNcPlanComplete(form) || item.nc.status === "in_progress") {
      inTreatment += 1;
    }
  }

  const pending = Math.max(total - finalized, 0);
  const progressPct = total > 0 ? Math.round((finalized / total) * 100) : 0;

  return { total, registered, inTreatment, finalized, pending, progressPct };
}

export function formatNcScore(score: number): string {
  return `${score},0`;
}

export function formatRelativeUpdate(timestamp: number | null): string {
  if (!timestamp) return "Sem alterações nesta sessão";
  const diffMs = Date.now() - timestamp;
  const diffMin = Math.max(Math.round(diffMs / 60000), 0);
  if (diffMin <= 0) return "Última atualização: agora";
  if (diffMin === 1) return "Última atualização: há 1 minuto";
  return `Última atualização: há ${diffMin} minutos`;
}

export function normalizeOptionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export function formsEqual(a: NcFormState, b: NcFormState): boolean {
  return (
    a.description === b.description &&
    a.root_cause === b.root_cause &&
    a.corrective_action === b.corrective_action &&
    a.responsible_name === b.responsible_name &&
    a.due_date === b.due_date &&
    a.priority === b.priority
  );
}

export function ncWorkflowStep(status: string | undefined): 1 | 2 | 3 {
  if (status === "closed") return 3;
  if (status === "in_progress") return 2;
  return 1;
}
