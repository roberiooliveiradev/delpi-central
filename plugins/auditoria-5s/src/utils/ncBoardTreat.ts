import type { NcCandidate, Nonconformity } from "../api/audit5sApi";
import type { NcBoardItem } from "../types/ncManagement";
import {
  defaultDueDate,
  type NcFormState,
  type NcTreatmentItem,
} from "./auditNc";

export function formFromNcBoardItem(item: NcBoardItem): NcFormState {
  return {
    description: item.description?.trim() ?? "",
    root_cause: item.root_cause?.trim() ?? "",
    corrective_action: item.corrective_action?.trim() ?? "",
    responsible_name: item.responsible_name?.trim() ?? "",
    due_date: item.due_date ?? defaultDueDate(),
    priority: (item.priority as NcFormState["priority"]) ?? "",
  };
}

export function nonconformityFromBoardItem(item: NcBoardItem): Nonconformity | null {
  if (!item.is_registered) return null;

  return {
    id: item.id,
    audit_id: item.audit_id,
    response_id: item.response_id,
    description: item.description ?? "",
    root_cause: item.root_cause,
    corrective_action: item.corrective_action,
    responsible_name: item.responsible_name ?? "",
    due_date: item.due_date ?? "",
    priority: item.priority as Nonconformity["priority"],
    status: item.status === "pending" ? "open" : item.status,
    criterion_code: item.criterion_code,
    criterion_description: item.criterion_description,
    senso_order: item.senso_order,
    senso_name: item.senso_name,
    created_at: item.created_at ?? undefined,
    updated_at: item.updated_at ?? undefined,
  };
}

export function buildBoardTreatmentItem(
  item: NcBoardItem,
  candidate: NcCandidate | null,
): NcTreatmentItem {
  return {
    criterionId: candidate?.id ?? item.response_id,
    responseId: item.response_id,
    code: item.criterion_code,
    criterionDescription: item.criterion_description,
    sensoOrder: item.senso_order,
    sensoName: item.senso_name,
    score: item.score ?? candidate?.response.score ?? 0,
    observation: candidate?.response.observation ?? null,
    evaluationAttachment: candidate?.response.attachment ?? null,
    nc: nonconformityFromBoardItem(item),
  };
}
