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

/** Identidade global Minha DELPI (cargo/contatos/foto) — só do usuário autenticado. */
export type MyPersonProfile = {
  job_title: string | null;
  phone_e164: string | null;
  mobile_e164: string | null;
  whatsapp_e164: string | null;
  has_photo: boolean;
};

export async function fetchMyPersonProfile(
  getAccessToken?: () => string | undefined,
  signal?: AbortSignal,
): Promise<MyPersonProfile | null> {
  const response = await fetch("/core-api/me/person-profile", {
    method: "GET",
    signal,
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(getAccessToken),
    },
  });
  if (!response.ok) return null;
  const profile = (await response.json()) as {
    job_title?: unknown;
    phone_e164?: unknown;
    mobile_e164?: unknown;
    whatsapp_e164?: unknown;
    has_photo?: unknown;
  };
  const asText = (value: unknown): string | null =>
    typeof value === "string" && value.trim() ? value.trim() : null;
  return {
    job_title: asText(profile.job_title),
    phone_e164: asText(profile.phone_e164),
    mobile_e164: asText(profile.mobile_e164),
    whatsapp_e164: asText(profile.whatsapp_e164),
    has_photo: Boolean(profile.has_photo),
  };
}

export async function fetchMyPersonProfilePhotoBlob(
  getAccessToken?: () => string | undefined,
  signal?: AbortSignal,
): Promise<Blob | null> {
  const profile = await fetchMyPersonProfile(getAccessToken, signal);
  if (!profile?.has_photo) return null;

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
