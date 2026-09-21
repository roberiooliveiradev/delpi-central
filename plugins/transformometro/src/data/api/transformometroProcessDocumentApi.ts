import type {
  ProcessDocument,
  ProcessDocumentList,
  ProcessDocumentSummary,
} from "../../types/processDocument";
import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";
import { parseApiEnvelope } from "./transformometroHttp";

function basePath(processoId: string): string {
  return `${TRANSFORMOMETRO_API_BASE}/processes/${processoId}/documents`;
}

export async function fetchProcessDocuments(
  processoId: string,
  getAccessToken?: () => string | undefined,
): Promise<ProcessDocumentSummary[]> {
  const response = await fetch(basePath(processoId), {
    headers: buildAuthHeaders(getAccessToken),
  });
  const data = await parseApiEnvelope<ProcessDocumentList>(response);
  return data.items ?? [];
}

export async function fetchProcessDocument(
  processoId: string,
  documentId: string,
  getAccessToken?: () => string | undefined,
): Promise<ProcessDocument> {
  const response = await fetch(`${basePath(processoId)}/${documentId}`, {
    headers: buildAuthHeaders(getAccessToken),
  });
  return parseApiEnvelope<ProcessDocument>(response);
}

export async function createProcessDocument(
  processoId: string,
  body: { title: string; content_md?: string },
  getAccessToken?: () => string | undefined,
): Promise<ProcessDocument> {
  const response = await fetch(basePath(processoId), {
    method: "POST",
    headers: {
      ...buildAuthHeaders(getAccessToken),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title: body.title,
      content_md: body.content_md ?? "",
    }),
  });
  return parseApiEnvelope<ProcessDocument>(response);
}

export async function updateProcessDocument(
  processoId: string,
  documentId: string,
  body: { title?: string; content_md?: string },
  getAccessToken?: () => string | undefined,
): Promise<ProcessDocument> {
  const response = await fetch(`${basePath(processoId)}/${documentId}`, {
    method: "PATCH",
    headers: {
      ...buildAuthHeaders(getAccessToken),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return parseApiEnvelope<ProcessDocument>(response);
}

export async function deleteProcessDocument(
  processoId: string,
  documentId: string,
  getAccessToken?: () => string | undefined,
): Promise<void> {
  const response = await fetch(`${basePath(processoId)}/${documentId}`, {
    method: "DELETE",
    headers: buildAuthHeaders(getAccessToken),
  });
  await parseApiEnvelope(response);
}
