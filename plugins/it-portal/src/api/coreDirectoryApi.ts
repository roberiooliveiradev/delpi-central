import { coreApiGet, coreApiPost } from "./httpClient";

export type DirectoryUser = { id: string; name: string; email?: string };
type DirectoryResponse = { items?: DirectoryUser[] };

/** Core e a fonte de verdade. Lista somente usuarios ativos; sem filtro de acesso ao app. */
export async function searchDirectoryUsers(query: string, signal?: AbortSignal): Promise<DirectoryUser[]> {
  const q = query.trim();
  if (q.length < 2) return [];
  const qs = new URLSearchParams({ q, limit: "15", include_self: "true" });
  const result = await coreApiGet<DirectoryResponse>(`/core-api/me/directory/users?${qs}`, signal);
  return Array.isArray(result.items) ? result.items : [];
}

/** Lookup devolve apenas usuarios ainda ativos. Falha de rede != conta inativa. */
export async function lookupDirectoryUser(userId: string, signal?: AbortSignal): Promise<DirectoryUser | null> {
  const result = await coreApiPost<DirectoryResponse>(
    "/core-api/me/directory/users/lookup",
    { ids: [userId] },
    signal,
  );
  return (result.items ?? []).find((row) => row.id === userId) ?? null;
}
