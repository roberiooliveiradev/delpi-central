import type {
  AdminAuditExportResponse,
  AdminAuditQuery,
  AdminExternalActionCatalogItem,
  AdminFutureApiOptions,
  AdminGuidelinePayload,
  AdminGuidelineVersion,
  AdminRagTestRequest,
  AdminRagTestResponse,
  AdminToolHealthResponse,
} from "./adminFutureTypes";

const FUTURE_API_BASE_URL = "/apps/minha-delpi-ai/api";

async function getFutureAuthHeaders(
  options: AdminFutureApiOptions = {},
): Promise<HeadersInit> {
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

async function parseFutureJsonResponse<T>(response: Response): Promise<T> {
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

/**
 * Endpoints planejados.
 *
 * Estes métodos existem para estabilizar o contrato do front.
 * Não devem ser chamados até o backend implementar as rotas.
 */

export async function testAdminRag(
  payload: AdminRagTestRequest,
  options: AdminFutureApiOptions = {},
): Promise<AdminRagTestResponse> {
  const response = await fetch(`${FUTURE_API_BASE_URL}/admin/rag/test`, {
    method: "POST",
    headers: await getFutureAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseFutureJsonResponse<AdminRagTestResponse>(response);
}

export async function listAdminGuidelineVersions(
  guidelineId: string,
  options: AdminFutureApiOptions = {},
): Promise<AdminGuidelineVersion[]> {
  const response = await fetch(
    `${FUTURE_API_BASE_URL}/admin/guidelines/${guidelineId}/versions`,
    {
      method: "GET",
      headers: await getFutureAuthHeaders(options),
    },
  );

  return parseFutureJsonResponse<AdminGuidelineVersion[]>(response);
}

export async function saveAdminGuidelineDraft(
  payload: AdminGuidelinePayload,
  options: AdminFutureApiOptions = {},
): Promise<AdminGuidelinePayload> {
  const response = await fetch(`${FUTURE_API_BASE_URL}/admin/guidelines`, {
    method: "POST",
    headers: await getFutureAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseFutureJsonResponse<AdminGuidelinePayload>(response);
}

export async function publishAdminGuideline(
  guidelineId: string,
  options: AdminFutureApiOptions = {},
): Promise<{ id: string; status: "active" }> {
  const response = await fetch(
    `${FUTURE_API_BASE_URL}/admin/guidelines/${guidelineId}/publish`,
    {
      method: "POST",
      headers: await getFutureAuthHeaders(options),
    },
  );

  return parseFutureJsonResponse<{ id: string; status: "active" }>(response);
}

export async function archiveAdminGuideline(
  guidelineId: string,
  options: AdminFutureApiOptions = {},
): Promise<{ id: string; status: "archived" }> {
  const response = await fetch(
    `${FUTURE_API_BASE_URL}/admin/guidelines/${guidelineId}/archive`,
    {
      method: "POST",
      headers: await getFutureAuthHeaders(options),
    },
  );

  return parseFutureJsonResponse<{ id: string; status: "archived" }>(response);
}

export async function listAdminExternalActions(
  options: AdminFutureApiOptions = {},
): Promise<AdminExternalActionCatalogItem[]> {
  const response = await fetch(`${FUTURE_API_BASE_URL}/admin/tools/actions`, {
    method: "GET",
    headers: await getFutureAuthHeaders(options),
  });

  return parseFutureJsonResponse<AdminExternalActionCatalogItem[]>(response);
}

export async function syncAdminOpenApiProviders(
  options: AdminFutureApiOptions = {},
): Promise<{ synced: boolean }> {
  const response = await fetch(`${FUTURE_API_BASE_URL}/admin/tools/openapi/sync`, {
    method: "POST",
    headers: await getFutureAuthHeaders(options),
  });

  return parseFutureJsonResponse<{ synced: boolean }>(response);
}

export async function testAdminExternalAction(
  actionId: string,
  options: AdminFutureApiOptions = {},
): Promise<{ id: string; ok: boolean; message?: string }> {
  const response = await fetch(
    `${FUTURE_API_BASE_URL}/admin/tools/actions/${actionId}/test`,
    {
      method: "POST",
      headers: await getFutureAuthHeaders(options),
    },
  );

  return parseFutureJsonResponse<{ id: string; ok: boolean; message?: string }>(
    response,
  );
}

export async function getAdminToolHealth(
  options: AdminFutureApiOptions = {},
): Promise<AdminToolHealthResponse> {
  const response = await fetch(`${FUTURE_API_BASE_URL}/admin/tools/health`, {
    method: "GET",
    headers: await getFutureAuthHeaders(options),
  });

  return parseFutureJsonResponse<AdminToolHealthResponse>(response);
}

export async function exportAdminAuditLogs(
  query: AdminAuditQuery,
  options: AdminFutureApiOptions = {},
): Promise<AdminAuditExportResponse> {
  const searchParams = new URLSearchParams();

  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      searchParams.set(key, String(value));
    }
  });

  const response = await fetch(
    `${FUTURE_API_BASE_URL}/admin/audit-logs/export?${searchParams.toString()}`,
    {
      method: "GET",
      headers: await getFutureAuthHeaders(options),
    },
  );

  return parseFutureJsonResponse<AdminAuditExportResponse>(response);
}
