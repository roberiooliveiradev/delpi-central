import { httpGet, httpPost } from "./httpClient";

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};

type DirectorySearchResponse = {
  items: DirectoryUser[];
};

export type SearchDirectoryUsersOptions = {
  /** Filtra quem já tem a app no portal (mesma regra de /me/apps). */
  appId?: string;
  /** Ex.: `tv-dashboard.write` quando o papel do share for Editor. */
  permission?: string;
};

/** Busca usuários da Minha DELPI (core-api). Persistência de share usa só `id`. */
export async function searchDirectoryUsers(
  query: string,
  limit = 10,
  signal?: AbortSignal,
  options?: SearchDirectoryUsersOptions,
): Promise<DirectoryUser[]> {
  const normalized = query.trim();
  if (normalized.length < 2) return [];

  const params = new URLSearchParams({
    q: normalized,
    limit: String(limit),
  });
  const appId = (options?.appId ?? "tv-dashboard").trim();
  if (appId) params.set("app", appId);
  const permission = options?.permission?.trim();
  if (permission) params.set("permission", permission);

  const payload = await httpGet<DirectorySearchResponse>(
    `/core-api/me/directory/users?${params.toString()}`,
    { signal },
  );

  return payload.items ?? [];
}

/** Resolve nomes/e-mails por id (UI). Shares no backend permanecem só com user id. */
export async function lookupDirectoryUsersByIds(
  ids: string[],
  signal?: AbortSignal,
): Promise<Map<string, DirectoryUser>> {
  const unique = [...new Set(ids.map((id) => id.trim()).filter(Boolean))];
  const map = new Map<string, DirectoryUser>();
  if (unique.length === 0) return map;

  try {
    const payload = await httpPost<DirectorySearchResponse>(
      "/core-api/me/directory/users/lookup",
      { ids: unique },
      { signal },
    );
    for (const item of payload.items ?? []) {
      if (item?.id) map.set(item.id, item);
    }
  } catch {
    /* ignore — lista cai no id cru */
  }
  return map;
}
