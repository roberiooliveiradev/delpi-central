import type {
  AdminAuditLog,
  AdminKnowledgeDocument,
  AdminKnowledgeDocumentsResponse,
  AdminLlmStatus,
  AdminMetricsSummary,
} from "./adminTypes";

const API_BASE_URL = "/apps/minha-delpi-ai/api";

type TokenProvider = () => string | undefined | Promise<string | undefined>;

type AdminApiOptions = {
  getAccessToken?: TokenProvider;
};

export type CreateKnowledgeDocumentPayload = {
  title: string;
  sourceType: string;
  sourceRef?: string;
  content: string;
  metadata?: Record<string, unknown>;
};

export type CreateKnowledgeDocumentResponse = {
  id: string;
  title: string;
  chunks: number;
};

export type UploadKnowledgeDocumentFilePayload = {
  file: File;
  title?: string;
  sourceType?: string;
  sourceRef?: string;
  metadata?: Record<string, unknown>;
};

async function getMultipartAuthHeaders(options: AdminApiOptions): Promise<HeadersInit> {
  const token = await options.getAccessToken?.();

  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

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

export type ListKnowledgeDocumentsParams = {
  search?: string;
  active?: "all" | "active" | "inactive";
  limit?: number;
  offset?: number;
};

export async function listKnowledgeDocuments(
  params: ListKnowledgeDocumentsParams = {},
  options: AdminApiOptions = {},
): Promise<AdminKnowledgeDocumentsResponse> {
  const query = new URLSearchParams();

  query.set("limit", String(params.limit ?? 10));
  query.set("offset", String(params.offset ?? 0));

  if (params.search?.trim()) {
    query.set("search", params.search.trim());
  }

  if (params.active === "active") {
    query.set("active", "true");
  }

  if (params.active === "inactive") {
    query.set("active", "false");
  }

  const response = await fetch(
    `${API_BASE_URL}/admin/knowledge/documents?${query.toString()}`,
    {
      method: "GET",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<AdminKnowledgeDocumentsResponse>(response);
}

export async function createKnowledgeDocument(
  payload: CreateKnowledgeDocumentPayload,
  options: AdminApiOptions = {},
): Promise<CreateKnowledgeDocumentResponse> {
  const response = await fetch(`${API_BASE_URL}/knowledge/documents`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<CreateKnowledgeDocumentResponse>(response);
}

export async function uploadKnowledgeDocumentFile(
  payload: UploadKnowledgeDocumentFilePayload,
  options: AdminApiOptions = {},
): Promise<CreateKnowledgeDocumentResponse> {
  const formData = new FormData();

  formData.set("file", payload.file);

  if (payload.title?.trim()) {
    formData.set("title", payload.title.trim());
  }

  if (payload.sourceType?.trim()) {
    formData.set("sourceType", payload.sourceType.trim());
  }

  if (payload.sourceRef?.trim()) {
    formData.set("sourceRef", payload.sourceRef.trim());
  }

  if (payload.metadata) {
    formData.set("metadata", JSON.stringify(payload.metadata));
  }

  const response = await fetch(`${API_BASE_URL}/admin/knowledge/documents/upload`, {
    method: "POST",
    headers: await getMultipartAuthHeaders(options),
    body: formData,
  });

  return parseJsonResponse<CreateKnowledgeDocumentResponse>(response);
}

export async function deleteKnowledgeDocument(
  documentId: string,
  options: AdminApiOptions = {},
): Promise<{ id: string; title: string; deleted: boolean }> {
  const response = await fetch(`${API_BASE_URL}/admin/knowledge/documents/${documentId}`, {
    method: "DELETE",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<{ id: string; title: string; deleted: boolean }>(response);
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


export async function reindexKnowledgeDocument(
  documentId: string,
  options: AdminApiOptions = {},
): Promise<CreateKnowledgeDocumentResponse & { active: boolean }> {
  const response = await fetch(
    `${API_BASE_URL}/admin/knowledge/documents/${documentId}/reindex`,
    {
      method: "POST",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<CreateKnowledgeDocumentResponse & { active: boolean }>(response);
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


export async function getAdminMetricsSummary(
  options: AdminApiOptions = {},
): Promise<AdminMetricsSummary> {
  const response = await fetch(`${API_BASE_URL}/admin/metrics/summary`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminMetricsSummary>(response);
}
