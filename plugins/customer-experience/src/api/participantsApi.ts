import {
  httpDownloadBlob,
  httpGet,
  httpPost,
  httpPostForm,
  unwrapEnvelope,
  type ApiEnvelope,
} from "./httpClient";
import type {
  CreateParticipantInput,
  Participant,
  ParticipantListResult,
} from "../types";

const API_BASE = "/apps/customer-experience-api";
const PARTICIPANTS = `${API_BASE}/participants`;

export async function listParticipants(params: {
  company?: string;
  visitDate?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<ParticipantListResult> {
  const query = new URLSearchParams();
  if (params.company) query.set("company", params.company);
  if (params.visitDate) query.set("visit_date", params.visitDate);
  if (params.limit != null) query.set("limit", String(params.limit));
  if (params.offset != null) query.set("offset", String(params.offset));

  const suffix = query.toString() ? `?${query.toString()}` : "";
  const response = await httpGet<ApiEnvelope<ParticipantListResult>>(`${PARTICIPANTS}${suffix}`);
  return unwrapEnvelope(response, "Não foi possível listar os participantes.");
}

export async function createParticipant(input: CreateParticipantInput): Promise<Participant> {
  const formData = new FormData();
  formData.append("full_name", input.fullName);
  formData.append("company_name", input.companyName);
  formData.append("visit_date", input.visitDate);
  if (input.participantInfo) formData.append("participant_info", input.participantInfo);
  if (input.thankYouMessage) formData.append("thank_you_message", input.thankYouMessage);
  formData.append("photo", input.photo);

  const response = await httpPostForm<ApiEnvelope<Participant>>(PARTICIPANTS, formData);
  return unwrapEnvelope(response, "Não foi possível cadastrar o participante.");
}

export async function deactivateParticipant(id: string): Promise<Participant> {
  const response = await httpPost<ApiEnvelope<Participant>>(`${PARTICIPANTS}/${id}/deactivate`);
  return unwrapEnvelope(response, "Não foi possível desativar o link.");
}

export async function downloadQr(id: string): Promise<Blob> {
  return httpDownloadBlob(`${PARTICIPANTS}/${id}/qr`);
}

export async function downloadFeedbackQr(id: string): Promise<Blob> {
  return httpDownloadBlob(`${PARTICIPANTS}/${id}/feedback-qr`);
}
