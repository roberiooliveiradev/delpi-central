import { httpGet } from "./httpClient";

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};

/**
 * Pesquisa paginada no diretório da Core API (não lista o universo completo).
 * Requer autenticação do portal; sem bypass Keycloak.
 */
export async function searchDirectoryUsers(
  query: string,
  limit = 10,
  signal?: AbortSignal,
): Promise<DirectoryUser[]> {
  const qs = new URLSearchParams({
    q: query,
    limit: String(Math.min(Math.max(limit, 1), 25)),
    include_self: "true",
    reveal_email: "true",
  });
  const payload = await httpGet<{ items?: DirectoryUser[] }>(
    `/core-api/me/directory/users?${qs.toString()}`,
    { signal },
  );
  return (payload.items ?? []).map((item) => ({
    id: item.id,
    name: item.name,
    email: item.email,
  }));
}
