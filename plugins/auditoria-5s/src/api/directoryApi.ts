import { httpGet } from "./httpClient";

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};

type DirectorySearchResponse = {
  items: DirectoryUser[];
};

export async function searchDirectoryUsers(
  query: string,
  limit = 10,
  signal?: AbortSignal,
  options?: { minLength?: number; includeSelf?: boolean },
): Promise<DirectoryUser[]> {
  const normalized = query.trim();
  const minLength = options?.minLength ?? 2;
  if (normalized.length < minLength) {
    return [];
  }

  const params = new URLSearchParams({
    q: normalized,
    limit: String(limit),
  });
  if (options?.includeSelf) {
    params.set("include_self", "true");
  }

  const payload = await httpGet<DirectorySearchResponse>(
    `/core-api/me/directory/users?${params.toString()}`,
    { signal },
  );

  return payload.items ?? [];
}
