import type {
  AtaGenerationRequest,
  AtaGenerationResult,
} from "../../ai/meetingMinuteGenerationPort";
import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";
import { parseApiEnvelope } from "./transformometroHttp";

export type AtaListItem = {
  id: string;
  unit_code: "01" | "02";
  title: string;
  minute_number?: string;
  meeting_type: string;
  meeting_date: string;
  status: string;
  signatures_done?: number;
  signatures_pending?: number;
  updated_at?: string;
};

export type AtaDetail = {
  minute: Record<string, unknown>;
  version: Record<string, unknown> | null;
  participants: Record<string, unknown>[];
  signers: Record<string, unknown>[];
  signatures: Record<string, unknown>[];
  viewer?: { is_signer: boolean; has_signed: boolean; can_sign_now: boolean };
};

export type SignatureProfile = {
  display_name: string;
  has_signature: boolean;
  updated_at?: string | null;
};

function query(params: Record<string, string | undefined>) {
  const value = new URLSearchParams();
  Object.entries(params).forEach(([key, item]) => item && value.set(key, item));
  return value.toString() ? `?${value}` : "";
}

async function request<T>(
  path: string,
  getAccessToken?: () => string | undefined,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}${path}`, {
    ...init,
    headers: {
      ...buildAuthHeaders(getAccessToken),
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers ?? {}),
    },
  });
  return parseApiEnvelope<T>(response);
}

export function listAtas(
  getAccessToken?: () => string | undefined,
  params: { unit_code?: string; status?: string } = {},
) {
  return request<{ items: AtaListItem[]; total: number }>(`/meeting-minutes${query(params)}`, getAccessToken);
}

export function getAta(id: string, getAccessToken?: () => string | undefined) {
  return request<AtaDetail>(`/meeting-minutes/${id}`, getAccessToken);
}

export function createAta(payload: Record<string, unknown>, getAccessToken?: () => string | undefined) {
  return request<AtaDetail>("/meeting-minutes", getAccessToken, { method: "POST", body: JSON.stringify(payload) });
}

type GenerateAtaApiData = {
  agenda_html?: string;
  body_html?: string;
  decisions_html?: string;
  pending_html?: string;
  observations_html?: string;
  title?: string | null;
  unitCode?: string;
  meetingDate?: string;
  source?: string;
};

export async function generateAtaFromTranscript(
  generationRequest: AtaGenerationRequest,
  getAccessToken?: () => string | undefined,
): Promise<AtaGenerationResult> {
  const data = await request<GenerateAtaApiData>("/meeting-minutes/generate-from-transcript", getAccessToken, {
    method: "POST",
    body: JSON.stringify({
      unitCode: generationRequest.unitCode,
      meetingDate: generationRequest.meetingDate,
      title: generationRequest.title,
      transcriptHtml: generationRequest.transcriptHtml,
      source: generationRequest.source,
    }),
  });

  return {
    agendaHtml: String(data.agenda_html ?? "<p></p>"),
    bodyHtml: String(data.body_html ?? "<p></p>"),
    decisionsHtml: String(data.decisions_html ?? "<p></p>"),
    pendingHtml: String(data.pending_html ?? "<p></p>"),
    observationsHtml: String(data.observations_html ?? "<p></p>"),
    title: data.title != null && String(data.title).trim() ? String(data.title) : undefined,
  };
}

export function updateAta(id: string, payload: Record<string, unknown>, getAccessToken?: () => string | undefined) {
  return request<AtaDetail>(`/meeting-minutes/${id}`, getAccessToken, { method: "PATCH", body: JSON.stringify(payload) });
}

export function setAtaSigners(id: string, signers: Record<string, unknown>[], getAccessToken?: () => string | undefined) {
  return request<{ signers: Record<string, unknown>[] }>(`/meeting-minutes/${id}/signers`, getAccessToken, {
    method: "PUT",
    body: JSON.stringify({ signers }),
  });
}

export async function searchDirectoryUsers(
  search: string,
  limit = 10,
  signal?: AbortSignal,
  getAccessToken?: () => string | undefined,
): Promise<Array<{ id: string; name: string; email: string }>> {
  const qs = new URLSearchParams({
    q: search,
    limit: String(limit),
    include_self: "true",
  });
  const response = await fetch(`/core-api/me/directory/users?${qs.toString()}`, {
    signal,
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(getAccessToken),
    },
  });
  if (!response.ok) {
    throw new Error("Não foi possível consultar o diretório de usuários.");
  }
  const payload = (await response.json()) as {
    items?: Array<{ id: string; name: string; email: string }>;
  };
  return payload.items ?? [];
}

export function sendAta(id: string, getAccessToken?: () => string | undefined) {
  return request<Record<string, unknown>>(`/meeting-minutes/${id}/send-for-signature`, getAccessToken, { method: "POST" });
}

export function finalizeAta(id: string, getAccessToken?: () => string | undefined) {
  return request<Record<string, unknown>>(`/meeting-minutes/${id}/finalize`, getAccessToken, { method: "POST" });
}

export function getAtaSignContext(id: string, getAccessToken?: () => string | undefined) {
  return request<Record<string, unknown>>(`/meeting-minutes/${id}/sign-context`, getAccessToken);
}

export function signAta(id: string, form: FormData, getAccessToken?: () => string | undefined) {
  return request<Record<string, unknown>>(`/meeting-minutes/${id}/signatures`, getAccessToken, {
    method: "POST",
    body: form,
    headers: { "Idempotency-Key": crypto.randomUUID() },
  });
}

export function refuseAta(id: string, reason: string, getAccessToken?: () => string | undefined) {
  return request<Record<string, unknown>>(`/meeting-minutes/${id}/signatures/refuse`, getAccessToken, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export function pendingAtas(getAccessToken?: () => string | undefined) {
  return request<{ items: AtaListItem[]; total: number }>("/meeting-minutes/pending-signatures", getAccessToken);
}

export function getSignatureProfile(getAccessToken?: () => string | undefined) {
  return request<SignatureProfile>("/signatures/me", getAccessToken);
}

export function updateSignatureProfile(payload: { display_name: string }, getAccessToken?: () => string | undefined) {
  return request<SignatureProfile>("/signatures/me", getAccessToken, { method: "PUT", body: JSON.stringify(payload) });
}

export function uploadSignature(blob: Blob, getAccessToken?: () => string | undefined) {
  const form = new FormData();
  form.append("signature", blob, "signature.png");
  return request<SignatureProfile>("/signatures/me/image", getAccessToken, { method: "POST", body: form });
}

export async function fetchSignatureImageBlob(
  getAccessToken?: () => string | undefined,
): Promise<Blob> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}/signatures/me/image`, {
    headers: buildAuthHeaders(getAccessToken),
  });
  if (!response.ok) {
    throw new Error("Assinatura pessoal não encontrada.");
  }
  return response.blob();
}

export async function fetchAtaSignatureImageBlob(
  minuteId: string,
  signatureId: string,
  getAccessToken?: () => string | undefined,
): Promise<Blob> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/meeting-minutes/${encodeURIComponent(minuteId)}/signatures/${encodeURIComponent(signatureId)}/image`,
    { headers: buildAuthHeaders(getAccessToken) },
  );
  if (!response.ok) {
    throw new Error("Imagem da assinatura não encontrada.");
  }
  return response.blob();
}

export function exportAtaPdfUrl(id: string): string {
  return `${TRANSFORMOMETRO_API_BASE}/meeting-minutes/${id}/export.pdf`;
}
