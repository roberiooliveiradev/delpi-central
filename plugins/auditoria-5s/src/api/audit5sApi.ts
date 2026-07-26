import { API_BASE } from "../constants/audit5s";
import type { AuditDashboardData, AuditDashboardFilterParams } from "../types/auditDashboard";
import type { NcBoardData, NcBoardFilterParams } from "../types/ncManagement";
import {
  type ApiEnvelope,
  httpDelete,
  httpGet,
  httpPatch,
  httpPost,
  httpPut,
  httpUploadForm,
  unwrapApiDelpiEnvelope,
} from "./httpClient";

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

export type CatalogSensoName = {
  catalog_version: number;
  senso_sort_order: number;
  name: string;
};

export type CatalogData = {
  branch_code: string;
  catalog_version: number;
  criteria_count: number;
  criteria: Criterion[];
  senso_names: CatalogSensoName[];
  last_published_at: string | null;
  last_published_by_user_id: string | null;
};

export type CatalogPublication = {
  id: string;
  branch_code: string;
  catalog_version: number;
  published_by_user_id: string | null;
  published_at: string;
  criteria_count: number;
  notes: string | null;
};

export type PublishCatalogPayload = {
  branch_code: string;
  criteria: Array<{
    senso_order: number;
    sort_order: number;
    code: string;
    description: string;
  }>;
  senso_names?: Array<{
    senso_sort_order: number;
    name: string;
  }>;
  notes?: string | null;
};

export type PublishCatalogResult = {
  branch_code: string;
  catalog_version: number;
  criteria_count: number;
  published_at: string;
  published_by_user_id: string | null;
  publication_id: string;
};

export type ResponseAttachment = {
  id: string;
  response_id: string;
  criterion_id?: string;
  file_name: string;
  original_name: string;
  mime_type: string | null;
  size_bytes: number;
  storage_path?: string;
  uploaded_by_user_id?: string;
  uploaded_at?: string;
};

export type AuditResponse = {
  id: string;
  criterion_id: string;
  score: number | null;
  is_not_applicable: boolean;
  observation: string | null;
  version: number;
  attachment?: ResponseAttachment | null;
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
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function createArea(branch: string, name: string) {
  const res = await httpPost<ApiEnvelope<AuditArea>>(`${API_BASE}/areas`, {
    branch_code: branch,
    name,
  });
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function fetchCatalog(branch: string) {
  const res = await httpGet<ApiEnvelope<CatalogData>>(`${API_BASE}/catalog?branch=${branch}`);
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function fetchCatalogPublications(branch: string) {
  const res = await httpGet<ApiEnvelope<CatalogPublication[]>>(
    `${API_BASE}/catalog/publications?branch=${branch}`,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function publishCatalog(payload: PublishCatalogPayload) {
  const res = await httpPut<ApiEnvelope<PublishCatalogResult>>(
    `${API_BASE}/catalog/publish`,
    payload,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function fetchAudits(branch: string) {
  const res = await httpGet<ApiEnvelope<AuditListItem[]>>(`${API_BASE}/audits?branch=${branch}`);
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function fetchAudit(auditId: string) {
  const res = await httpGet<ApiEnvelope<AuditDetail>>(`${API_BASE}/audits/${auditId}`);
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function joinAudit(auditId: string) {
  const res = await httpPost<ApiEnvelope<AuditDetail>>(`${API_BASE}/audits/${auditId}/join`, {});
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function deleteAudit(auditId: string) {
  await httpPost<ApiEnvelope<null>>(`${API_BASE}/audits/${auditId.trim()}/delete`, {});
}

export async function forceDeleteAudit(auditId: string) {
  await httpPost<ApiEnvelope<null>>(
    `${API_BASE}/audits/${auditId.trim()}/force-delete`,
    {},
  );
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
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function updateAudit(
  auditId: string,
  payload: {
    audit_date?: string;
    area_id?: string;
    area_responsible?: string;
    shift?: string;
    auditors?: Array<{ user_id: string; display_name: string }>;
  },
) {
  const res = await httpPatch<ApiEnvelope<AuditDetail>>(
    `${API_BASE}/audits/${auditId.trim()}`,
    payload,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
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
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function uploadResponseAttachment(
  auditId: string,
  criterionId: string,
  file: File,
) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await httpUploadForm<ApiEnvelope<ResponseAttachment>>(
    `${API_BASE}/audits/${auditId}/responses/${criterionId}/attachments`,
    formData,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function deleteResponseAttachment(
  auditId: string,
  criterionId: string,
  attachmentId: string,
) {
  const res = await httpDelete<ApiEnvelope<{ deleted: boolean }>>(
    `${API_BASE}/audits/${auditId}/responses/${criterionId}/attachments/${attachmentId}`,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function completeEvaluation(auditId: string) {
  const res = await httpPost<ApiEnvelope<AuditDetail>>(
    `${API_BASE}/audits/${auditId}/complete-evaluation`,
    {},
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function reopenEvaluation(auditId: string) {
  const res = await httpPost<ApiEnvelope<AuditDetail>>(
    `${API_BASE}/audits/${auditId.trim()}/reopen-evaluation`,
    {},
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
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
  responsible_user_id?: string | null;
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
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function fetchNonconformities(auditId: string) {
  const res = await httpGet<ApiEnvelope<Nonconformity[]>>(
    `${API_BASE}/audits/${auditId}/nonconformities`,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function createNonconformity(
  auditId: string,
  payload: {
    response_id: string;
    description: string;
    responsible_name: string;
    responsible_user_id?: string | null;
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
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function updateNonconformity(
  ncId: string,
  payload: Partial<{
    description: string;
    root_cause: string | null;
    corrective_action: string | null;
    responsible_name: string;
    responsible_user_id: string | null;
    due_date: string;
    priority: NcPriority | null;
  }>,
) {
  const res = await httpPatch<ApiEnvelope<Nonconformity>>(
    `${API_BASE}/nonconformities/${ncId}`,
    payload,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function fetchAuditNcAttachments(auditId: string) {
  const res = await httpGet<ApiEnvelope<NcAttachment[]>>(
    `${API_BASE}/audits/${auditId}/nc-attachments`,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function uploadNcAttachment(ncId: string, attachmentType: NcAttachmentType, file: File) {
  const formData = new FormData();
  formData.append("attachment_type", attachmentType);
  formData.append("file", file);
  const res = await httpUploadForm<ApiEnvelope<NcAttachment>>(
    `${API_BASE}/nonconformities/${ncId}/attachments`,
    formData,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function completeNcAction(ncId: string) {
  const res = await httpPost<ApiEnvelope<Nonconformity>>(
    `${API_BASE}/nonconformities/${ncId}/complete-action`,
    {},
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function reopenNcAction(ncId: string) {
  const res = await httpPost<ApiEnvelope<Nonconformity>>(
    `${API_BASE}/nonconformities/${ncId.trim()}/reopen-action`,
    {},
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function fetchNcActions(ncId: string) {
  const res = await httpGet<ApiEnvelope<NcAction[]>>(
    `${API_BASE}/nonconformities/${ncId}/actions`,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function addNcAction(
  ncId: string,
  description: string,
  mentionedUserIds: string[] = [],
) {
  const res = await httpPost<ApiEnvelope<NcAction>>(
    `${API_BASE}/nonconformities/${ncId}/actions`,
    {
      description,
      mentioned_user_ids: mentionedUserIds,
    },
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function closeAudit(auditId: string) {
  const res = await httpPost<ApiEnvelope<AuditDetail>>(
    `${API_BASE}/audits/${auditId}/close`,
    {},
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

export async function closeAuditWithoutNcTreatment(auditId: string) {
  const res = await httpPost<ApiEnvelope<AuditDetail>>(
    `${API_BASE}/audits/${auditId.trim()}/close-without-nc-treatment`,
    {},
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

function buildDashboardQuery(params: AuditDashboardFilterParams): string {
  const search = new URLSearchParams();
  search.set("branch", params.branch);
  search.set("start_date", params.start_date);
  search.set("end_date", params.end_date);
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
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}

function buildNcBoardQuery(params: NcBoardFilterParams): string {
  const search = new URLSearchParams();
  search.set("branch", params.branch);
  search.set("page", String(params.page));
  search.set("page_size", String(params.page_size));
  if (params.start_date) search.set("start_date", params.start_date);
  if (params.end_date) search.set("end_date", params.end_date);
  if (params.area_id) search.set("area_id", params.area_id);
  if (params.shift) search.set("shift", params.shift);
  if (params.status) search.set("status", params.status);
  if (params.priority) search.set("priority", params.priority);
  if (params.responsible) search.set("responsible", params.responsible);
  if (params.responsible_user_id) {
    search.set("responsible_user_id", params.responsible_user_id);
  }
  if (params.overdue_only) search.set("overdue_only", "true");
  if (params.pending_only) search.set("pending_only", "true");
  if (params.senso_order != null) search.set("senso_order", String(params.senso_order));
  if (params.search) search.set("search", params.search);
  if (params.sort) search.set("sort", params.sort);
  return search.toString();
}

export async function fetchNcBoard(params: NcBoardFilterParams) {
  const query = buildNcBoardQuery(params);
  const res = await httpGet<ApiEnvelope<NcBoardData>>(
    `${API_BASE}/nonconformities?${query}`,
  );
  return unwrapApiDelpiEnvelope(res, "Erro na API de auditoria 5S");
}
