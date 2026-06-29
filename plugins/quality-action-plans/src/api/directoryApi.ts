import { httpGet } from "./httpClient";

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
  /** Id do app no portal (ex.: quality-action-plans) — mesma regra de GET /me/apps. */
  appId?: string;
  /** Código de permissão exigido (alternativa ao appId). */
  permission?: string;
  signal?: AbortSignal;
};

export async function searchDirectoryUsers(
  query: string,
  options: DirectorySearchOptions = {},
): Promise<DirectoryUser[]> {
  const normalized = query.trim();
  if (normalized.length < 2) {
    return [];
  }

  const limit = options.limit ?? 10;
  const params = new URLSearchParams({
    q: normalized,
    limit: String(limit),
  });

  if (options.appId) {
    params.set("app", options.appId);
  }
  if (options.permission) {
    params.set("permission", options.permission);
  }

  const payload = await httpGet<DirectorySearchResponse>(
    `/core-api/me/directory/users?${params.toString()}`,
    { signal: options.signal },
  );

  return payload.items ?? [];
}
