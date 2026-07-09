import type { RevisaoEvidence, RevisaoEvidenceList, RevisaoEvidenceType } from "../../types/revisaoEvidence";
import { canPreviewAttachedFile } from "../../utils/evidenceFilePreview";
import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

async function parseEnvelope<T>(response: Response): Promise<T> {
  const body = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || !body.success) {
    throw new Error(body.message || `Erro HTTP ${response.status}`);
  }
  return body.data;
}

export async function fetchRevisaoEvidencias(
  revisaoId: string,
  getAccessToken?: () => string | undefined
): Promise<RevisaoEvidence[]> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}/revisoes/${revisaoId}/evidencias`, {
    headers: buildAuthHeaders(getAccessToken),
  });
  const data = await parseEnvelope<RevisaoEvidenceList>(response);
  return data.items ?? [];
}

export async function uploadRevisaoEvidence(
  revisaoId: string,
  params: {
    tipo: RevisaoEvidenceType;
    file?: File;
    descricao?: string;
    urlExterna?: string;
  },
  getAccessToken?: () => string | undefined
): Promise<RevisaoEvidence> {
  const form = new FormData();
  form.set("tipo", params.tipo);
  if (params.descricao) form.set("descricao", params.descricao);
  if (params.urlExterna) form.set("url_externa", params.urlExterna);
  if (params.file) form.append("file", params.file);

  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}/revisoes/${revisaoId}/evidencias`, {
    method: "POST",
    headers: buildAuthHeaders(getAccessToken),
    body: form,
  });
  return parseEnvelope<RevisaoEvidence>(response);
}

export async function deleteRevisaoEvidence(
  revisaoId: string,
  evidenciaId: string,
  getAccessToken?: () => string | undefined
): Promise<void> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/revisoes/${revisaoId}/evidencias/${evidenciaId}`,
    {
      method: "DELETE",
      headers: buildAuthHeaders(getAccessToken),
    }
  );
  await parseEnvelope(response);
}

export function revisaoEvidenceFileUrl(revisaoId: string, evidenciaId: string): string {
  return `${TRANSFORMOMETRO_API_BASE}/revisoes/${revisaoId}/evidencias/${evidenciaId}/arquivo`;
}

export async function fetchRevisaoEvidenceObjectUrl(
  revisaoId: string,
  evidenciaId: string,
  getAccessToken?: () => string | undefined
): Promise<string> {
  const response = await fetch(revisaoEvidenceFileUrl(revisaoId, evidenciaId), {
    headers: buildAuthHeaders(getAccessToken),
  });
  if (!response.ok) {
    throw new Error(`Erro HTTP ${response.status}`);
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export function formatEvidenceFileSize(bytes?: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function inferEvidenceTypeFromFile(file: File): RevisaoEvidenceType {
  const mime = file.type.toLowerCase();
  if (mime.startsWith("image/")) return "foto";
  if (
    mime === "application/pdf" ||
    mime.includes("word") ||
    mime.includes("spreadsheet") ||
    mime.includes("excel")
  ) {
    return "documento";
  }
  return "anexo";
}

export function createPendingUploadId(): string {
  return `pending-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function canPreviewEvidence(evidence: RevisaoEvidence): boolean {
  return canPreviewAttachedFile(evidence);
}
