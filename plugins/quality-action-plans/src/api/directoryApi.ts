import { httpGet, unwrapApiDelpiEnvelope, type ApiEnvelope } from "./httpClient";

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};

type DirectorySearchResponse = {
  items: DirectoryUser[];
};

export type DirectorySearchOptions = {
  limit?: number;
  /** Lista inicial ao abrir o seletor (sem filtro de texto). */
  browse?: boolean;
  signal?: AbortSignal;
};

const ASSIGNABLE_USERS_BASE = "/apps/api-delpi/quality/action-plans/assignable-users";

export async function searchDirectoryUsers(
  query: string,
  options: DirectorySearchOptions = {},
): Promise<DirectoryUser[]> {
  const normalized = query.trim();
  const limit = options.limit ?? 20;
  const browse = options.browse ?? (!normalized);

  if (!browse && normalized.length < 2) {
    return [];
  }

  const params = new URLSearchParams({
    limit: String(limit),
  });

  if (normalized) {
    params.set("q", normalized);
  }

  const envelope = await httpGet<ApiEnvelope<DirectorySearchResponse>>(
    `${ASSIGNABLE_USERS_BASE}?${params.toString()}`,
    { signal: options.signal },
  );

  const data = unwrapApiDelpiEnvelope(envelope, "Erro ao buscar usuários atribuíveis.");
  return data.items ?? [];
}
