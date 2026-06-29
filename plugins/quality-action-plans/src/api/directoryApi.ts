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
): Promise<DirectoryUser[]> {
  const normalized = query.trim();
  if (normalized.length < 2) {
    return [];
  }

  const params = new URLSearchParams({
    q: normalized,
    limit: String(limit),
  });

  const payload = await httpGet<DirectorySearchResponse>(
    `/core-api/me/directory/users?${params.toString()}`,
    { signal },
  );

  return payload.items ?? [];
}
