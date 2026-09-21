import { buildAuthHeaders } from "./transformometroApiBase";

export type DirectoryUserHit = {
  id: string;
  name: string;
  email?: string;
};

/** Resolve nomes de exibição via POST /core-api/me/directory/users/lookup. */
export async function lookupDirectoryUsers(
  userIds: readonly string[],
  signal?: AbortSignal,
  getAccessToken?: () => string | undefined,
): Promise<DirectoryUserHit[]> {
  const ids = [...new Set(userIds.map((id) => id.trim()).filter(Boolean))];
  if (ids.length === 0) return [];

  const response = await fetch("/core-api/me/directory/users/lookup", {
    method: "POST",
    signal,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...buildAuthHeaders(getAccessToken),
    },
    body: JSON.stringify({ ids }),
  });
  if (!response.ok) {
    throw new Error("Não foi possível consultar o diretório de usuários.");
  }
  const payload = (await response.json()) as {
    items?: Array<{ id?: unknown; name?: unknown; email?: unknown }>;
  };
  return (payload.items ?? [])
    .map((item) => ({
      id: typeof item.id === "string" ? item.id : "",
      name: typeof item.name === "string" ? item.name.trim() : "",
      email: typeof item.email === "string" ? item.email : undefined,
    }))
    .filter((item) => item.id && item.name);
}

export async function fetchMyPersonProfilePhotoBlob(
  getAccessToken?: () => string | undefined,
  signal?: AbortSignal,
): Promise<Blob | null> {
  const meta = await fetch("/core-api/me/person-profile", {
    method: "GET",
    signal,
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(getAccessToken),
    },
  });
  if (!meta.ok) return null;
  const profile = (await meta.json()) as { has_photo?: unknown };
  if (!profile.has_photo) return null;

  const photo = await fetch("/core-api/me/person-profile/photo", {
    method: "GET",
    signal,
    headers: {
      Accept: "application/octet-stream",
      ...buildAuthHeaders(getAccessToken),
    },
  });
  if (!photo.ok) return null;
  return photo.blob();
}
