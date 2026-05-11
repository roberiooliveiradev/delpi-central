import type {
  AdminAuditLog,
  AdminKnowledgeDocument,
  AdminLlmStatus,
} from "./adminTypes";

const API_BASE_URL = "/apps/minha-delpi-ai/api";

type TokenProvider = () => string | undefined | Promise<string | undefined>;

type AdminApiOptions = {
  getAccessToken?: TokenProvider;
};

async function getAuthHeaders(options: AdminApiOptions): Promise<HeadersInit> {
  const token = await options.getAccessToken?.();

  if (!token) {
    return {
      "Content-Type": "application/json",
    };
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      payload?.errors?.[0]?.message ??
      payload?.message ??
      "Erro ao comunicar com a administração do Minha DELPI Chat.";

    throw new Error(message);
  }

  return payload as T;
}

export async function getLlmStatus(
  options: AdminApiOptions = {},
): Promise<AdminLlmStatus> {
  const response = await fetch(`${API_BASE_URL}/admin/llm/status`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminLlmStatus>(response);
}

export async function listKnowledgeDocuments(
  options: AdminApiOptions = {},
): Promise<AdminKnowledgeDocument[]> {
  const response = await fetch(`${API_BASE_URL}/admin/knowledge/documents?limit=100`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminKnowledgeDocument[]>(response);
}

export async function deactivateKnowledgeDocument(
  documentId: string,
  options: AdminApiOptions = {},
): Promise<AdminKnowledgeDocument> {
  const response = await fetch(
    `${API_BASE_URL}/admin/knowledge/documents/${documentId}/deactivate`,
    {
      method: "POST",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<AdminKnowledgeDocument>(response);
}


export async function reactivateKnowledgeDocument(
  documentId: string,
  options: AdminApiOptions = {},
): Promise<AdminKnowledgeDocument> {
  const response = await fetch(
    `${API_BASE_URL}/admin/knowledge/documents/${documentId}/reactivate`,
    {
      method: "POST",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<AdminKnowledgeDocument>(response);
}

export async function listAuditLogs(
  options: AdminApiOptions = {},
): Promise<AdminAuditLog[]> {
  const response = await fetch(`${API_BASE_URL}/admin/audit-logs?limit=100`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminAuditLog[]>(response);
}
