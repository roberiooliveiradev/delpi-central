import { httpBlob, httpForm, httpGet, httpJson } from "./httpClient";

const API = "/apps/cipa-api";

export type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export type MinuteListItem = {
  id: string;
  unit_code: string;
  title: string;
  minute_number: string;
  meeting_type: string;
  meeting_date: string;
  status: string;
  responsible_name?: string | null;
  signatures_done?: number;
  signatures_pending?: number;
  updated_at?: string;
};

export type MinuteViewerContext = {
  user_id: string | null;
  is_signer: boolean;
  has_signed: boolean;
  can_sign_now: boolean;
};

export type MinuteDetail = {
  minute: Record<string, unknown>;
  version: Record<string, unknown> | null;
  participants: Record<string, unknown>[];
  signers: Record<string, unknown>[];
  signatures: Record<string, unknown>[];
  action_items: Record<string, unknown>[];
  versions: Record<string, unknown>[];
  /** Relação do usuário autenticado com a ata (API decide; MFE renderiza). */
  viewer?: MinuteViewerContext;
};

function unwrap<T>(envelope: ApiEnvelope<T>): T {
  if (!envelope?.success) {
    throw new Error(envelope?.message || "Falha na API CIPA.");
  }
  return envelope.data;
}

export async function listMinutes(
  params: Record<string, string | number | boolean | undefined>,
  signal?: AbortSignal,
) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === "") return;
    qs.set(key, String(value));
  });
  const envelope = await httpGet<ApiEnvelope<{ items: MinuteListItem[]; total: number }>>(
    `${API}/minutes?${qs.toString()}`,
    { signal },
  );
  return unwrap(envelope);
}

export async function getMinute(id: string, signal?: AbortSignal) {
  const envelope = await httpGet<ApiEnvelope<MinuteDetail>>(`${API}/minutes/${id}`, { signal });
  return unwrap(envelope);
}

export async function createMinute(body: Record<string, unknown>) {
  const envelope = await httpJson<ApiEnvelope<MinuteDetail>>("POST", `${API}/minutes`, body);
  return unwrap(envelope);
}

export async function updateMinute(id: string, body: Record<string, unknown>) {
  const envelope = await httpJson<ApiEnvelope<MinuteDetail>>("PATCH", `${API}/minutes/${id}`, body);
  return unwrap(envelope);
}

export async function deleteMinute(id: string) {
  const envelope = await httpJson<ApiEnvelope<{ minute: Record<string, unknown> }>>(
    "DELETE",
    `${API}/minutes/${id}`,
  );
  return unwrap(envelope);
}

export async function setSigners(id: string, signers: Record<string, unknown>[]) {
  const envelope = await httpJson<ApiEnvelope<{ signers: Record<string, unknown>[] }>>(
    "PUT",
    `${API}/minutes/${id}/signers`,
    { signers },
  );
  return unwrap(envelope);
}

export async function sendForSignature(id: string) {
  const envelope = await httpJson<ApiEnvelope<{ minute: Record<string, unknown> }>>(
    "POST",
    `${API}/minutes/${id}/send-for-signature`,
  );
  return unwrap(envelope);
}

export async function getSignContext(id: string, signal?: AbortSignal) {
  const envelope = await httpGet<ApiEnvelope<Record<string, unknown>>>(
    `${API}/minutes/${id}/sign-context`,
    { signal },
  );
  return unwrap(envelope);
}

export async function signMinute(
  id: string,
  form: FormData,
  idempotencyKey: string,
) {
  const envelope = await httpForm<ApiEnvelope<Record<string, unknown>>>(
    `${API}/minutes/${id}/signatures`,
    form,
    { idempotencyKey },
  );
  return unwrap(envelope);
}

export async function refuseMinute(id: string, reason: string) {
  const envelope = await httpJson<ApiEnvelope<Record<string, unknown>>>(
    "POST",
    `${API}/minutes/${id}/signatures/refuse`,
    { reason },
  );
  return unwrap(envelope);
}

export async function finalizeMinute(id: string) {
  const envelope = await httpJson<ApiEnvelope<Record<string, unknown>>>(
    "POST",
    `${API}/minutes/${id}/finalize`,
  );
  return unwrap(envelope);
}

export async function createVersion(id: string, body: Record<string, unknown>) {
  const envelope = await httpJson<ApiEnvelope<Record<string, unknown>>>(
    "POST",
    `${API}/minutes/${id}/versions`,
    body,
  );
  return unwrap(envelope);
}

export async function getAudit(id: string, signal?: AbortSignal) {
  const envelope = await httpGet<ApiEnvelope<{ items: Record<string, unknown>[] }>>(
    `${API}/minutes/${id}/audit`,
    { signal },
  );
  return unwrap(envelope);
}

export async function exportPdf(id: string) {
  return httpBlob(`${API}/minutes/${id}/export.pdf`);
}

export async function exportFilteredPdfs(
  params: Record<string, string | number | boolean | undefined>,
) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === "") return;
    qs.set(key, String(value));
  });
  return httpBlob(`${API}/minutes/export-filtered.zip?${qs.toString()}`);
}

export async function getSignatureImage(
  minuteId: string,
  signatureId: string,
  signal?: AbortSignal,
) {
  return httpBlob(`${API}/minutes/${minuteId}/signatures/${signatureId}/image`, {
    signal,
  });
}

export async function pendingSignatures(signal?: AbortSignal) {
  const envelope = await httpGet<ApiEnvelope<{ items: MinuteListItem[]; total: number }>>(
    `${API}/minutes/pending-signatures`,
    { signal },
  );
  return unwrap(envelope);
}

export async function searchDirectoryUsers(query: string, limit = 10, signal?: AbortSignal) {
  // include_self: quem cria a ata também pode ser participante/signatário.
  const qs = new URLSearchParams({ q: query, limit: String(limit), include_self: "true" });
  const payload = await httpGet<{ items?: DirectoryUser[] }>(
    `/core-api/me/directory/users?${qs.toString()}`,
    { signal },
  );
  return payload.items ?? [];
}

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};

export type CipaAccessPayload = {
  admin: boolean;
  can_view: boolean;
  can_manage: boolean;
  can_sign: boolean;
  units: Array<{
    id: "01" | "02";
    label: string;
    view: boolean;
    manage: boolean;
    sign: boolean;
  }>;
};

export async function fetchCipaAccess(signal?: AbortSignal) {
  const envelope = await httpGet<ApiEnvelope<CipaAccessPayload>>(`${API}/access`, { signal });
  return unwrap(envelope);
}

export type MySignatureProfile = {
  user_id: string;
  display_name: string;
  has_signature: boolean;
  updated_at?: string | null;
};

export async function getMySignatureProfile(signal?: AbortSignal) {
  const envelope = await httpGet<ApiEnvelope<MySignatureProfile>>(
    `${API}/signatures/me`,
    { signal },
  );
  return unwrap(envelope);
}

export async function updateMySignatureProfile(
  body: { display_name: string },
  signal?: AbortSignal,
) {
  const envelope = await httpJson<ApiEnvelope<MySignatureProfile>>(
    "PUT",
    `${API}/signatures/me`,
    body,
    { signal },
  );
  return unwrap(envelope);
}

export async function uploadMySignatureImage(blob: Blob, signal?: AbortSignal) {
  const form = new FormData();
  form.append("signature", blob, "signature.png");
  const envelope = await httpForm<ApiEnvelope<MySignatureProfile>>(
    `${API}/signatures/me/image`,
    form,
    { signal },
  );
  return unwrap(envelope);
}

export async function fetchMySignatureImageBlob(signal?: AbortSignal) {
  return httpBlob(`${API}/signatures/me/image`, { signal });
}

export type CipaMember = {
  id: string;
  unit_code: string;
  user_id: string;
  display_name: string;
  role: string;
  mandate_start: string;
  mandate_end?: string | null;
  is_active: boolean;
  sort_order?: number;
  created_at?: string;
  updated_at?: string;
  deleted_at?: string | null;
};

export async function listCipaMembers(
  unitCode: string,
  options?: {
    activeOn?: string;
    includeInactive?: boolean;
    signal?: AbortSignal;
  },
) {
  const qs = new URLSearchParams({ unit_code: unitCode });
  if (options?.activeOn) qs.set("active_on", options.activeOn);
  if (options?.includeInactive) qs.set("include_inactive", "true");
  const envelope = await httpGet<ApiEnvelope<CipaMember[]>>(
    `${API}/members?${qs.toString()}`,
    { signal: options?.signal },
  );
  return unwrap(envelope);
}

export async function createCipaMember(body: {
  unit_code: string;
  user_id: string;
  display_name: string;
  role: string;
  mandate_start: string;
  mandate_end?: string | null;
  sort_order?: number;
}) {
  const envelope = await httpJson<ApiEnvelope<CipaMember>>("POST", `${API}/members`, body);
  return unwrap(envelope);
}

export async function updateCipaMember(
  memberId: string,
  body: {
    display_name?: string;
    role?: string;
    mandate_start?: string;
    mandate_end?: string | null;
    is_active?: boolean;
    sort_order?: number;
  },
) {
  const envelope = await httpJson<ApiEnvelope<CipaMember>>(
    "PATCH",
    `${API}/members/${memberId}`,
    body,
  );
  return unwrap(envelope);
}

export async function endCipaMember(memberId: string, mandateEnd?: string | null) {
  const envelope = await httpJson<ApiEnvelope<CipaMember>>(
    "POST",
    `${API}/members/${memberId}/end`,
    { mandate_end: mandateEnd ?? null },
  );
  return unwrap(envelope);
}

export async function deleteCipaMember(memberId: string) {
  const envelope = await httpJson<ApiEnvelope<CipaMember>>(
    "DELETE",
    `${API}/members/${memberId}`,
  );
  return unwrap(envelope);
}

/* —— SIPAT —— */

export type SipatQuestionType =
  | "single_choice"
  | "multi_choice"
  | "likert_5"
  | "yes_no"
  | "text_short"
  | "text_long";

export type SipatQuestion = {
  id?: string;
  position?: number;
  question_type: SipatQuestionType;
  label: string;
  help_text?: string | null;
  is_required?: boolean;
  options?: string[] | null;
};

export type SipatSurvey = {
  id: string;
  unit_code: string;
  title: string;
  description?: string | null;
  status: "draft" | "published" | "closed";
  public_token?: string | null;
  public_url?: string | null;
  qr_filename?: string | null;
  opens_at?: string | null;
  closes_at?: string | null;
  response_count: number;
  created_at?: string;
  updated_at?: string;
};

export type SipatTemplate = {
  id: string;
  title: string;
  description: string;
  question_count: number;
};

export type SipatSurveyDetail = {
  survey: SipatSurvey;
  questions: SipatQuestion[];
};

export type SipatSummary = {
  survey: SipatSurvey;
  response_count: number;
  questions: Array<{
    question_id: string;
    label: string;
    question_type: string;
    answer_count: number;
    counts?: Record<string, number>;
    sample_texts?: string[];
  }>;
};

export async function listSipatSurveys(unitCode: string, signal?: AbortSignal) {
  const envelope = await httpGet<
    ApiEnvelope<{ items: SipatSurvey[]; templates: SipatTemplate[]; unit_code: string }>
  >(`${API}/sipat/surveys?unit_code=${encodeURIComponent(unitCode)}`, { signal });
  return unwrap(envelope);
}

export async function getSipatSurvey(id: string, signal?: AbortSignal) {
  const envelope = await httpGet<ApiEnvelope<SipatSurveyDetail>>(
    `${API}/sipat/surveys/${id}`,
    { signal },
  );
  return unwrap(envelope);
}

export async function createSipatSurvey(body: Record<string, unknown>) {
  const envelope = await httpJson<ApiEnvelope<SipatSurveyDetail>>(
    "POST",
    `${API}/sipat/surveys`,
    body,
  );
  return unwrap(envelope);
}

export async function updateSipatSurvey(id: string, body: Record<string, unknown>) {
  const envelope = await httpJson<ApiEnvelope<SipatSurveyDetail>>(
    "PATCH",
    `${API}/sipat/surveys/${id}`,
    body,
  );
  return unwrap(envelope);
}

export async function applySipatTemplate(id: string, templateId: string) {
  const envelope = await httpJson<ApiEnvelope<SipatSurveyDetail>>(
    "POST",
    `${API}/sipat/surveys/${id}/apply-template`,
    { template_id: templateId },
  );
  return unwrap(envelope);
}

export async function cloneSipatSurvey(id: string) {
  const envelope = await httpJson<ApiEnvelope<SipatSurveyDetail>>(
    "POST",
    `${API}/sipat/surveys/${id}/clone`,
  );
  return unwrap(envelope);
}

export async function publishSipatSurvey(id: string) {
  const envelope = await httpJson<ApiEnvelope<SipatSurveyDetail>>(
    "POST",
    `${API}/sipat/surveys/${id}/publish`,
  );
  return unwrap(envelope);
}

export async function closeSipatSurvey(id: string) {
  const envelope = await httpJson<ApiEnvelope<SipatSurveyDetail>>(
    "POST",
    `${API}/sipat/surveys/${id}/close`,
  );
  return unwrap(envelope);
}

export async function deleteSipatSurvey(id: string) {
  const envelope = await httpJson<ApiEnvelope<{ survey: SipatSurvey }>>(
    "DELETE",
    `${API}/sipat/surveys/${id}`,
  );
  return unwrap(envelope);
}

export async function getSipatSummary(id: string, signal?: AbortSignal) {
  const envelope = await httpGet<ApiEnvelope<SipatSummary>>(
    `${API}/sipat/surveys/${id}/summary`,
    { signal },
  );
  return unwrap(envelope);
}

export async function downloadSipatQr(id: string) {
  return httpBlob(`${API}/sipat/surveys/${id}/qr`);
}

export async function downloadSipatExcel(id: string) {
  return httpBlob(`${API}/sipat/surveys/${id}/export.xlsx`);
}
