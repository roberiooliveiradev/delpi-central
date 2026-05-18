import type {
  AdminAuditExportResponse,
  AdminAgentSimulateRequest,
  AdminAgentSimulateResponse,
  AdminAgentSpecialization,
  AdminAgentSpecializationPresetsResponse,
  AdminAgentSpecializationResponse,
  AdminSecurityConfig,
  AdminSecurityEventsResponse,
  AdminSecurityScanResponse,
  AdminSecuritySummary,
  AdminSpecializedAgentsResponse,
  AdminAuditLogDetailResponse,
  AdminAuditLogsResponse,
  AdminAuditQuery,
  AdminAuditTimelineResponse,
  AdminExternalActionCatalogItem,
  AdminGuideline,
  AdminGuidelineCategory,
  AdminGuidelineEnvironment,
  AdminGuidelineStatus,
  AdminGuidelineVersion,
  AdminGuidelineVersionComparison,
  AdminKnowledgeDocument,
  AdminKnowledgeDocumentsResponse,
  AdminKnowledgeIngestionPreviewResponse,
  AdminKnowledgeIngestionPipelineStats,
  AdminResponseCandidatesResponse,
  AdminResponseEvaluation,
  AdminResponseEvaluationContext,
  AdminResponseEvaluationSummary,
  UpdateKnowledgeDocumentMetadataPayload,
  AdminLlmStatus,
  AdminMetricsSummary,
  AdminRbacSummary,
  AdminRagTestRequest,
  AdminRagTestResponse,
  AdminToolHealthResponse,
} from "./adminTypes";

const API_BASE_URL = "/apps/minha-delpi-ai/api";

type TokenProvider = () => string | undefined | Promise<string | undefined>;

type AdminApiOptions = {
  getAccessToken?: TokenProvider;
};

export type KnowledgeCuratorialFields = {
  category?: string;
  tags?: string[] | string;
  namespace?: string;
  domain?: string;
  priority?: number;
  qualityScore?: number;
};

export type CreateKnowledgeDocumentPayload = {
  title: string;
  sourceType: string;
  sourceRef?: string;
  content: string;
  metadata?: Record<string, unknown>;
} & KnowledgeCuratorialFields;

export type CreateKnowledgeDocumentResponse = {
  id: string;
  title: string;
  chunks: number;
  duplicate?: boolean;
  skipped?: boolean;
  pipeline?: AdminKnowledgeIngestionPipelineStats;
};

export type PreviewKnowledgeIngestionPayload = {
  content: string;
  title?: string;
  sourceType?: string;
  sourceRef?: string;
  metadata?: Record<string, unknown>;
};

export type UploadKnowledgeDocumentFilePayload = {
  file: File;
  title?: string;
  sourceType?: string;
  sourceRef?: string;
  metadata?: Record<string, unknown>;
} & KnowledgeCuratorialFields;

function buildCuratorialMetadata(
  fields: KnowledgeCuratorialFields,
): Record<string, unknown> {
  const metadata: Record<string, unknown> = { scope: "global" };

  if (fields.category?.trim()) {
    metadata.category = fields.category.trim();
  }

  if (fields.namespace?.trim()) {
    metadata.namespace = fields.namespace.trim();
  }

  if (fields.domain?.trim()) {
    metadata.domain = fields.domain.trim();
  }

  if (fields.priority !== undefined && fields.priority !== null) {
    metadata.priority = fields.priority;
  }

  if (fields.qualityScore !== undefined && fields.qualityScore !== null) {
    metadata.qualityScore = fields.qualityScore;
  }

  if (fields.tags) {
    const tags = Array.isArray(fields.tags)
      ? fields.tags
      : fields.tags.split(",").map((tag) => tag.trim());

    metadata.tags = tags.filter(Boolean);
  }

  return metadata;
}

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


export type SaveAdminGuidelinePayload = {
  id?: string;
  title: string;
  description: string;
  content: string;
  category: AdminGuidelineCategory;
  environment?: AdminGuidelineEnvironment;
  status: AdminGuidelineStatus;
  metadata?: Record<string, unknown>;
};

export async function listAdminGuidelines(
  options: AdminApiOptions = {},
): Promise<AdminGuideline[]> {
  const response = await fetch(`${API_BASE_URL}/admin/guidelines`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminGuideline[]>(response);
}



export async function compareAdminGuidelineVersions(
  guidelineId: string,
  fromVersion: number,
  toVersion: number,
  options: AdminApiOptions = {},
): Promise<AdminGuidelineVersionComparison> {
  const params = new URLSearchParams({
    fromVersion: String(fromVersion),
    toVersion: String(toVersion),
  });

  const response = await fetch(
    `${API_BASE_URL}/admin/guidelines/${guidelineId}/versions/compare?${params.toString()}`,
    {
      method: "GET",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<AdminGuidelineVersionComparison>(response);
}

export async function restoreAdminGuidelineVersion(
  guidelineId: string,
  version: number,
  options: AdminApiOptions = {},
): Promise<AdminGuideline> {
  const response = await fetch(
    `${API_BASE_URL}/admin/guidelines/${guidelineId}/versions/${version}/restore`,
    {
      method: "POST",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<AdminGuideline>(response);
}

export async function listAdminGuidelineVersions(
  guidelineId: string,
  options: AdminApiOptions = {},
): Promise<AdminGuidelineVersion[]> {
  const response = await fetch(`${API_BASE_URL}/admin/guidelines/${guidelineId}/versions`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminGuidelineVersion[]>(response);
}

export async function saveAdminGuideline(
  payload: SaveAdminGuidelinePayload,
  options: AdminApiOptions = {},
): Promise<AdminGuideline> {
  const response = await fetch(`${API_BASE_URL}/admin/guidelines`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<AdminGuideline>(response);
}

export async function publishAdminGuideline(
  guidelineId: string,
  options: AdminApiOptions = {},
): Promise<AdminGuideline> {
  const response = await fetch(`${API_BASE_URL}/admin/guidelines/${guidelineId}/publish`, {
    method: "POST",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminGuideline>(response);
}

export async function archiveAdminGuideline(
  guidelineId: string,
  options: AdminApiOptions = {},
): Promise<AdminGuideline> {
  const response = await fetch(`${API_BASE_URL}/admin/guidelines/${guidelineId}/archive`, {
    method: "POST",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminGuideline>(response);
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
  category?: string;
  namespace?: string;
  domain?: string;
  tag?: string;
  sourceType?: string;
  limit?: number;
  offset?: number;
};

export async function previewKnowledgeIngestion(
  payload: PreviewKnowledgeIngestionPayload,
  options: AdminApiOptions = {},
): Promise<AdminKnowledgeIngestionPreviewResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/knowledge/ingest/preview`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<AdminKnowledgeIngestionPreviewResponse>(response);
}

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

  if (params.category?.trim()) {
    query.set("category", params.category.trim());
  }

  if (params.namespace?.trim()) {
    query.set("namespace", params.namespace.trim());
  }

  if (params.domain?.trim()) {
    query.set("domain", params.domain.trim());
  }

  if (params.tag?.trim()) {
    query.set("tag", params.tag.trim());
  }

  if (params.sourceType?.trim()) {
    query.set("sourceType", params.sourceType.trim());
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
  const { category, tags, namespace, domain, priority, qualityScore, metadata, ...rest } =
    payload;

  const response = await fetch(`${API_BASE_URL}/knowledge/documents`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify({
      ...rest,
      metadata: {
        ...buildCuratorialMetadata({
          category,
          tags,
          namespace,
          domain,
          priority,
          qualityScore,
        }),
        ...metadata,
      },
    }),
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

  const { category, tags, namespace, domain, priority, qualityScore, metadata } = payload;

  if (category?.trim()) {
    formData.set("category", category.trim());
  }

  if (tags) {
    formData.set(
      "tags",
      Array.isArray(tags) ? tags.join(",") : tags,
    );
  }

  if (namespace?.trim()) {
    formData.set("namespace", namespace.trim());
  }

  if (domain?.trim()) {
    formData.set("domain", domain.trim());
  }

  if (priority !== undefined && priority !== null) {
    formData.set("priority", String(priority));
  }

  if (qualityScore !== undefined && qualityScore !== null) {
    formData.set("qualityScore", String(qualityScore));
  }

  if (metadata) {
    formData.set("metadata", JSON.stringify(metadata));
  }

  const response = await fetch(`${API_BASE_URL}/admin/knowledge/documents/upload`, {
    method: "POST",
    headers: await getMultipartAuthHeaders(options),
    body: formData,
  });

  return parseJsonResponse<CreateKnowledgeDocumentResponse>(response);
}

export async function updateKnowledgeDocumentMetadata(
  documentId: string,
  payload: UpdateKnowledgeDocumentMetadataPayload,
  options: AdminApiOptions = {},
): Promise<AdminKnowledgeDocument> {
  const response = await fetch(
    `${API_BASE_URL}/admin/knowledge/documents/${documentId}/metadata`,
    {
      method: "PATCH",
      headers: await getAuthHeaders(options),
      body: JSON.stringify(payload),
    },
  );

  return parseJsonResponse<AdminKnowledgeDocument>(response);
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

function buildAuditQueryParams(query: AdminAuditQuery = {}): string {
  const searchParams = new URLSearchParams();

  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      searchParams.set(key, String(value));
    }
  });

  return searchParams.toString();
}

export async function listAdminAgentSpecializationPresets(
  options: AdminApiOptions = {},
): Promise<AdminAgentSpecializationPresetsResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/agents/specializations/catalog`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminAgentSpecializationPresetsResponse>(response);
}

export async function listAdminSpecializedAgents(
  options: AdminApiOptions = {},
): Promise<AdminSpecializedAgentsResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/agents/specialized`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminSpecializedAgentsResponse>(response);
}

export async function getAdminAgentSpecialization(
  agentId: string,
  options: AdminApiOptions = {},
): Promise<AdminAgentSpecializationResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/agents/${agentId}/specialization`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminAgentSpecializationResponse>(response);
}

export async function saveAdminAgentSpecialization(
  payload: { specialization: AdminAgentSpecialization | { enabled: false } },
  agentId: string,
  options: AdminApiOptions = {},
): Promise<AdminAgentSpecializationResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/agents/${agentId}/specialization`, {
    method: "PUT",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<AdminAgentSpecializationResponse>(response);
}

export async function getAdminSecurityConfig(
  options: AdminApiOptions = {},
): Promise<AdminSecurityConfig> {
  const response = await fetch(`${API_BASE_URL}/admin/security/config`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminSecurityConfig>(response);
}

export async function getAdminSecuritySummary(
  hours = 24,
  options: AdminApiOptions = {},
): Promise<AdminSecuritySummary> {
  const response = await fetch(`${API_BASE_URL}/admin/security/summary?hours=${hours}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminSecuritySummary>(response);
}

export type ListAdminSecurityEventsParams = {
  limit?: number;
  offset?: number;
  action?: string;
  userId?: string;
  dateFrom?: string;
  dateTo?: string;
};

export async function listAdminSecurityEvents(
  params: ListAdminSecurityEventsParams = {},
  options: AdminApiOptions = {},
): Promise<AdminSecurityEventsResponse> {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 25));
  query.set("offset", String(params.offset ?? 0));

  if (params.action?.trim()) {
    query.set("action", params.action.trim());
  }

  if (params.userId?.trim()) {
    query.set("userId", params.userId.trim());
  }

  if (params.dateFrom?.trim()) {
    query.set("dateFrom", params.dateFrom.trim());
  }

  if (params.dateTo?.trim()) {
    query.set("dateTo", params.dateTo.trim());
  }

  const response = await fetch(`${API_BASE_URL}/admin/security/events?${query.toString()}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminSecurityEventsResponse>(response);
}

export async function scanAdminSecurityInput(
  payload: { message: string; context?: string },
  options: AdminApiOptions = {},
): Promise<AdminSecurityScanResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/security/scan`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<AdminSecurityScanResponse>(response);
}

export async function getAdminResponseEvaluationSummary(
  options: AdminApiOptions = {},
): Promise<AdminResponseEvaluationSummary> {
  const response = await fetch(`${API_BASE_URL}/admin/responses/evaluations/summary`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminResponseEvaluationSummary>(response);
}

export type ListAdminResponseCandidatesParams = {
  search?: string;
  limit?: number;
  offset?: number;
};

export async function listAdminResponseCandidates(
  params: ListAdminResponseCandidatesParams = {},
  options: AdminApiOptions = {},
): Promise<AdminResponseCandidatesResponse> {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));

  if (params.search?.trim()) {
    query.set("search", params.search.trim());
  }

  const response = await fetch(
    `${API_BASE_URL}/admin/responses/candidates?${query.toString()}`,
    {
      method: "GET",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<AdminResponseCandidatesResponse>(response);
}

export async function getAdminResponseEvaluationContext(
  messageId: string,
  score: number,
  options: AdminApiOptions = {},
): Promise<AdminResponseEvaluationContext> {
  const query = new URLSearchParams();
  query.set("score", String(score));

  const response = await fetch(
    `${API_BASE_URL}/admin/responses/messages/${messageId}/evaluation-context?${query.toString()}`,
    {
      method: "GET",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<AdminResponseEvaluationContext>(response);
}

export type SaveAdminResponseEvaluationPayload = {
  messageId: string;
  score: number;
  comment?: string;
};

export async function saveAdminResponseEvaluation(
  payload: SaveAdminResponseEvaluationPayload,
  options: AdminApiOptions = {},
): Promise<AdminResponseEvaluation> {
  const response = await fetch(`${API_BASE_URL}/admin/responses/evaluations`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<AdminResponseEvaluation>(response);
}

export async function listAuditLogs(
  query: AdminAuditQuery = {},
  options: AdminApiOptions = {},
): Promise<AdminAuditLogsResponse> {
  const queryString = buildAuditQueryParams(query);
  const suffix = queryString ? `?${queryString}` : "";

  const response = await fetch(`${API_BASE_URL}/admin/audit-logs${suffix}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminAuditLogsResponse>(response);
}

export async function getAdminAuditLogDetail(
  logId: number,
  options: AdminApiOptions = {},
): Promise<AdminAuditLogDetailResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/audit-logs/${logId}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminAuditLogDetailResponse>(response);
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

export async function simulateAdminAgent(
  payload: AdminAgentSimulateRequest,
  options: AdminApiOptions = {},
): Promise<AdminAgentSimulateResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/agent/simulate`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<AdminAgentSimulateResponse>(response);
}

export async function testAdminRag(
  payload: AdminRagTestRequest,
  options: AdminApiOptions = {},
): Promise<AdminRagTestResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/rag/test`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<AdminRagTestResponse>(response);
}


export async function getAdminRbacSummary(
  options: AdminApiOptions = {},
): Promise<AdminRbacSummary> {
  const response = await fetch(`${API_BASE_URL}/admin/rbac/summary`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminRbacSummary>(response);
}

export async function getAdminToolHealth(
  _options: AdminApiOptions = {},
): Promise<AdminToolHealthResponse> {
  return {
    items: [
      {
        id: "external-actions-catalog",
        label: "Catálogo de actions",
        description: "Health técnico dedicado ainda não exposto pelo backend.",
        status: "unknown",
      },
    ],
  };
}

export async function listAdminExternalActions(
  options: AdminApiOptions = {},
): Promise<AdminExternalActionCatalogItem[]> {
  const response = await fetch(`${API_BASE_URL}/admin/external-actions`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminExternalActionCatalogItem[]>(response);
}

export async function getAdminAuditTimeline(
  query: AdminAuditQuery = {},
  options: AdminApiOptions = {},
): Promise<AdminAuditTimelineResponse> {
  const queryString = buildAuditQueryParams(query);
  const suffix = queryString ? `?${queryString}` : "";

  const response = await fetch(`${API_BASE_URL}/admin/audit-logs/timeline${suffix}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AdminAuditTimelineResponse>(response);
}

export async function exportAdminAuditLogs(
  query: AdminAuditQuery,
  options: AdminApiOptions = {},
): Promise<AdminAuditExportResponse> {
  const queryString = buildAuditQueryParams(query);

  const response = await fetch(
    `${API_BASE_URL}/admin/audit-logs/export?${queryString}`,
    {
      method: "GET",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<AdminAuditExportResponse>(response);
}

export async function exportAdminAuditLogsCsv(
  query: AdminAuditQuery,
  options: AdminApiOptions = {},
): Promise<Blob> {
  const params = new URLSearchParams(buildAuditQueryParams(query));
  params.set("format", "csv");

  const response = await fetch(`${API_BASE_URL}/admin/audit-logs/export?${params.toString()}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  if (!response.ok) {
    throw new Error(`Exportação CSV falhou (${response.status})`);
  }

  return response.blob();
}
