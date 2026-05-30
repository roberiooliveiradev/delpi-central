import { API_BASE } from "../constants/audit5s";
import type { AuditDashboardData, AuditDashboardFilterParams } from "../types/auditDashboard";
import { type ApiEnvelope, httpGet, httpPatch, httpPost, httpPut, httpUploadForm } from "./httpClient";

export type AuditArea = {
  id: string;
  branch_code: string;
  name: string;
  active: boolean;
};

export type AuditListItem = {
  id: string;
  audit_code: string;
  audit_date: string;
  area_name: string;
  area_responsible: string;
  shift: string;
  status: string;
  overall_score_pct: number | null;
  auditor_names?: string | null;
};

export type Criterion = {
  id: string;
  code: string;
  description: string;
  sort_order: number;
  senso_order: number;
  senso_name: string;
};

export type AuditResponse = {
  id: string;
  criterion_id: string;
  score: number | null;
  is_not_applicable: boolean;
  observation: string | null;
  version: number;
};

export type AuditDetail = {
  id: string;
  audit_code: string;
  branch_code: string;
  audit_date: string;
  area_id: string;
  area_name: string;
  area_responsible: string;
  shift: string;
  status: string;
  overall_score_pct: number | null;
  scores: {
    overall_percentual: number | null;
    sensos: Array<{ senso_order: number; percentual: number | null }>;
  };
  progress: { total: number; scored: number; pending: number };
  criteria: Criterion[];
  responses: AuditResponse[];
  auditors: Array<{ user_id: string; display_name: string }>;
};

export async function fetchAreas(branch: string) {
  const res = await httpGet<ApiEnvelope<AuditArea[]>>(`${API_BASE}/areas?branch=${branch}`);
  return res.data;
}

export async function createArea(branch: string, name: string) {
  const res = await httpPost<ApiEnvelope<AuditArea>>(`${API_BASE}/areas`, {
    branch_code: branch,
    name,
  });
  return res.data;
}

export async function fetchAudits(branch: string) {
  const res = await httpGet<ApiEnvelope<AuditListItem[]>>(`${API_BASE}/audits?branch=${branch}`);
  return res.data;
}

export async function fetchAudit(auditId: string) {
  const res = await httpGet<ApiEnvelope<AuditDetail>>(`${API_BASE}/audits/${auditId}`);
  return res.data;
}

export async function joinAudit(auditId: string) {
  const res = await httpPost<ApiEnvelope<AuditDetail>>(`${API_BASE}/audits/${auditId}/join`, {});
  return res.data;
}

export async function deleteAudit(auditId: string) {
  await httpPost<ApiEnvelope<null>>(`${API_BASE}/audits/${auditId.trim()}/delete`, {});
}

export async function createAudit(payload: {
  branch_code: string;
  audit_date: string;
  area_id: string;
  area_responsible: string;
  shift: string;
  auditors?: Array<{ user_id: string; display_name: string }>;
}) {
  const res = await httpPost<ApiEnvelope<AuditDetail>>(`${API_BASE}/audits`, payload);
  return res.data;
}

export async function saveResponse(
  auditId: string,
  criterionId: string,
  payload: {
    score: number | null;
    is_not_applicable: boolean;
    observation?: string | null;
    version?: number | null;
  },
) {
  const res = await httpPut<ApiEnvelope<{ response: AuditResponse; audit: AuditDetail }>>(
    `${API_BASE}/audits/${auditId}/responses/${criterionId}`,
    payload,
  );
  return res.data;
}

export async function completeEvaluation(auditId: string) {
  const res = await httpPost<ApiEnvelope<AuditDetail>>(
    `${API_BASE}/audits/${auditId}/complete-evaluation`,
    {},
  );
  return res.data;
}

export type NcCandidate = Criterion & {
  response: AuditResponse;
};

export type Nonconformity = {
  id: string;
  audit_id: string;
  response_id: string;
  description: string;
  root_cause: string | null;
  corrective_action: string | null;
  responsible_name: string;
  due_date: string;
  priority: NcPriority | null;
  status: string;
  criterion_code: string;
  criterion_description: string;
  senso_order: number;
  senso_name: string;
  created_at?: string;
  updated_at?: string;
};

export type NcPriority = "high" | "medium" | "low";
export type NcStatus = "open" | "in_progress" | "closed";

export type NcAttachmentType = "before" | "after";

export type NcAttachment = {
  id: string;
  nonconformity_id: string;
  attachment_type: NcAttachmentType;
  original_name: string;
  stored_name: string;
  mime_type: string | null;
  size_bytes: number;
  uploaded_by_user_id?: string;
  created_at?: string;
};

export type NcAttachmentMap = Record<string, Partial<Record<NcAttachmentType, NcAttachment>>>;

export type NcAction = {
  id: string;
  description: string;
  actor_display_name: string;
  created_at: string;
};

export async function fetchNcCandidates(auditId: string) {
  const res = await httpGet<ApiEnvelope<NcCandidate[]>>(
    `${API_BASE}/audits/${auditId}/nc-candidates`,
  );
  return res.data;
}

export async function fetchNonconformities(auditId: string) {
  const res = await httpGet<ApiEnvelope<Nonconformity[]>>(
    `${API_BASE}/audits/${auditId}/nonconformities`,
  );
  return res.data;
}

export async function createNonconformity(
  auditId: string,
  payload: {
    response_id: string;
    description: string;
    responsible_name: string;
    due_date: string;
    root_cause?: string | null;
    corrective_action?: string | null;
    priority?: NcPriority | null;
  },
) {
  const res = await httpPost<ApiEnvelope<Nonconformity>>(
    `${API_BASE}/audits/${auditId}/nonconformities`,
    payload,
  );
  return res.data;
}

export async function updateNonconformity(
  ncId: string,
  payload: Partial<{
    description: string;
    root_cause: string | null;
    corrective_action: string | null;
    responsible_name: string;
    due_date: string;
    priority: NcPriority | null;
  }>,
) {
  const res = await httpPatch<ApiEnvelope<Nonconformity>>(
    `${API_BASE}/nonconformities/${ncId}`,
    payload,
  );
  return res.data;
}

export async function fetchAuditNcAttachments(auditId: string) {
  const res = await httpGet<ApiEnvelope<NcAttachment[]>>(
    `${API_BASE}/audits/${auditId}/nc-attachments`,
  );
  return res.data;
}

export async function uploadNcAttachment(ncId: string, attachmentType: NcAttachmentType, file: File) {
  const formData = new FormData();
  formData.append("attachment_type", attachmentType);
  formData.append("file", file);
  const res = await httpUploadForm<ApiEnvelope<NcAttachment>>(
    `${API_BASE}/nonconformities/${ncId}/attachments`,
    formData,
  );
  return res.data;
}

export async function completeNcAction(ncId: string) {
  const res = await httpPost<ApiEnvelope<Nonconformity>>(
    `${API_BASE}/nonconformities/${ncId}/complete-action`,
    {},
  );
  return res.data;
}

export async function fetchNcActions(ncId: string) {
  const res = await httpGet<ApiEnvelope<NcAction[]>>(
    `${API_BASE}/nonconformities/${ncId}/actions`,
  );
  return res.data;
}

export async function addNcAction(ncId: string, description: string) {
  const res = await httpPost<ApiEnvelope<NcAction>>(
    `${API_BASE}/nonconformities/${ncId}/actions`,
    { description },
  );
  return res.data;
}

export async function closeAudit(auditId: string) {
  const res = await httpPost<ApiEnvelope<AuditDetail>>(
    `${API_BASE}/audits/${auditId}/close`,
    {},
  );
  return res.data;
}

function buildDashboardQuery(params: AuditDashboardFilterParams): string {
  const search = new URLSearchParams();
  search.set("branch", params.branch);
  search.set("date_start", params.date_start);
  search.set("date_end", params.date_end);
  search.set("granularity", params.granularity);
  search.set("page", String(params.page));
  search.set("page_size", String(params.page_size));
  if (params.area_id) search.set("area_id", params.area_id);
  if (params.shift) search.set("shift", params.shift);
  if (params.audit_status) search.set("audit_status", params.audit_status);
  if (params.senso_order != null) search.set("senso_order", String(params.senso_order));
  return search.toString();
}

export async function fetchAudit5sDashboard(params: AuditDashboardFilterParams) {
  const query = buildDashboardQuery(params);
  const res = await httpGet<ApiEnvelope<AuditDashboardData>>(
    `${API_BASE}/analytics/dashboard?${query}`,
  );
  return res.data;
}
