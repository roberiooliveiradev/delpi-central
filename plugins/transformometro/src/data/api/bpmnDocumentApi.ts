import { BpmnDocumentError } from "@delpi/bpmn-editor";

import {
  TRANSFORMOMETRO_API_BASE,
  buildAuthHeaders,
} from "./transformometroApiBase";

type GetToken = (() => string | undefined) | undefined;

/** Metadados do documento BPMN nativo do processo (V1 / ADR-006). */
export type ProcessBpmnDocument = {
  document_id: string;
  processo_id: string;
  version: number;
  working_copy_sha256: string;
  created_by?: string;
  updated_by?: string;
  created_at?: string;
  updated_at?: string;
};

export type ProcessBpmnRevision = {
  revision_id: string;
  document_id: string;
  revision_number: number;
  artifact_sha256: string;
  origin: "explicit" | "restore";
  source_revision_number?: number | null;
  name?: string | null;
  description?: string | null;
  created_by?: string;
  created_by_name?: string | null;
  created_at?: string;
};

type EnvelopeFail = {
  success?: boolean;
  message?: string;
  data?: Record<string, unknown> | null;
};

/**
 * Converte o envelope fail() do Transformômetro no erro de transporte do
 * document host — preserva status/kind para o SaveMachine classificar
 * (CONFLICT, VALIDATION_BLOCKED) sem bifurcar semântica.
 */
function toDocumentError(
  status: number,
  body: EnvelopeFail | null,
  fallback: string,
): BpmnDocumentError {
  const data = (body?.data ?? {}) as Record<string, unknown>;
  const kind = typeof data.error_kind === "string" ? data.error_kind : "";
  const code =
    status === 409 || kind === "version_conflict"
      ? "CONFLICT"
      : status === 400 ||
          kind === "unsafe_artifact" ||
          kind === "artifact_error"
        ? "VALIDATION_BLOCKED"
        : kind === "dual_mode_forbidden"
          ? "DUAL_MODE_FORBIDDEN"
          : undefined;
  return new BpmnDocumentError(status, {
    success: false,
    error: code
      ? { code, message: body?.message ?? fallback, details: data }
      : undefined,
    message: body?.message ?? fallback,
  }, fallback);
}

async function docRequest<T>(
  path: string,
  getAccessToken: GetToken,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}${path}`,
    {
      ...init,
      headers: {
        ...buildAuthHeaders(getAccessToken),
        ...(init?.headers ?? {}),
      },
    },
  );
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    const text = await response.text();
    if (!response.ok) {
      throw toDocumentError(response.status, null, `HTTP ${response.status}`);
    }
    return text as T;
  }
  const body = (await response.json()) as EnvelopeFail & { data?: T };
  if (!response.ok || body.success === false) {
    throw toDocumentError(
      response.status,
      body,
      `HTTP ${response.status}`,
    );
  }
  return body.data as T;
}

const docBase = (processoId: string) =>
  `/processos/${processoId}/bpmn-document`;

/** `null` quando o processo não tem documento nativo (probe segura). */
export async function fetchProcessBpmnDocument(
  processoId: string,
  getAccessToken: GetToken,
): Promise<{ document: ProcessBpmnDocument; version: number } | null> {
  try {
    return await docRequest(docBase(processoId), getAccessToken);
  } catch (err) {
    if (err instanceof BpmnDocumentError && err.status === 404) return null;
    throw err;
  }
}

export function createProcessBpmnDocument(
  processoId: string,
  xml: string | null,
  getAccessToken: GetToken,
): Promise<ProcessBpmnDocument> {
  return docRequest(docBase(processoId), getAccessToken, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ xml }),
  });
}

export function fetchProcessBpmnWorkingCopy(
  processoId: string,
  getAccessToken: GetToken,
): Promise<{ xml: string; version: number; sha256: string }> {
  return docRequest(`${docBase(processoId)}/working-copy`, getAccessToken);
}

export function saveProcessBpmnWorkingCopy(
  processoId: string,
  xml: string,
  expectedVersion: number,
  getAccessToken: GetToken,
): Promise<ProcessBpmnDocument> {
  return docRequest(`${docBase(processoId)}/working-copy`, getAccessToken, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "If-Match": `"v${expectedVersion}"`,
    },
    body: JSON.stringify({ xml }),
  });
}

export function deleteProcessBpmnDocument(
  processoId: string,
  getAccessToken: GetToken,
): Promise<{ deleted: boolean; document_id: string }> {
  return docRequest(docBase(processoId), getAccessToken, {
    method: "DELETE",
  });
}

export function fetchProcessBpmnRevisions(
  processoId: string,
  getAccessToken: GetToken,
): Promise<{ items: ProcessBpmnRevision[]; document: ProcessBpmnDocument }> {
  return docRequest(`${docBase(processoId)}/revisions`, getAccessToken);
}

export function createProcessBpmnRevision(
  processoId: string,
  expectedVersion: number,
  meta: { name?: string; description?: string },
  getAccessToken: GetToken,
): Promise<ProcessBpmnRevision> {
  return docRequest(`${docBase(processoId)}/revisions`, getAccessToken, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "If-Match": `"v${expectedVersion}"`,
    },
    body: JSON.stringify(meta),
  });
}

export function fetchProcessBpmnRevision(
  processoId: string,
  revisionNumber: number,
  getAccessToken: GetToken,
): Promise<{ revision: ProcessBpmnRevision }> {
  return docRequest(
    `${docBase(processoId)}/revisions/${revisionNumber}`,
    getAccessToken,
  );
}

export function fetchProcessBpmnRevisionXml(
  processoId: string,
  revisionNumber: number,
  getAccessToken: GetToken,
): Promise<string> {
  return docRequest<string>(
    `${docBase(processoId)}/revisions/${revisionNumber}/export`,
    getAccessToken,
  );
}

export function restoreProcessBpmnRevision(
  processoId: string,
  revisionNumber: number,
  expectedVersion: number,
  getAccessToken: GetToken,
): Promise<ProcessBpmnDocument> {
  return docRequest(
    `${docBase(processoId)}/revisions/${revisionNumber}/restore`,
    getAccessToken,
    {
      method: "POST",
      headers: { "If-Match": `"v${expectedVersion}"` },
    },
  );
}

export function validateProcessBpmnWorkingCopy(
  processoId: string,
  xml: string | null,
  getAccessToken: GetToken,
): Promise<{
  document: ProcessBpmnDocument;
  report: {
    evaluated_stages?: string[];
    not_evaluated_stages?: string[];
    issues?: unknown[];
    fatal?: string;
  };
}> {
  return docRequest(
    `${docBase(processoId)}/working-copy/validate`,
    getAccessToken,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ xml }),
    },
  );
}

export function exportProcessBpmnWorkingCopy(
  processoId: string,
  getAccessToken: GetToken,
): Promise<string> {
  return docRequest<string>(
    `${docBase(processoId)}/working-copy/export`,
    getAccessToken,
  );
}
