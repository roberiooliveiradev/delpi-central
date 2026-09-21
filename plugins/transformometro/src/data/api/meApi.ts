import { buildAuthHeaders } from "./transformometroApiBase";

export type MeProfile = {
  id: string;
  name: string;
};

/** Primeiro nome da sessão. Não usa e-mail nem persiste PII. */
export function greetingFirstNameFromProfile(profile: {
  name?: string | null;
  email?: string | null;
}): string | null {
  const trimmed = (profile.name ?? "").trim();
  if (!trimmed || trimmed.includes("@")) return null;
  const firstName = trimmed.split(/\s+/)[0] || "";
  if (!firstName || firstName.includes("@")) return null;
  return firstName;
}

export async function fetchMeProfile(
  getAccessToken?: () => string | undefined,
  signal?: AbortSignal,
): Promise<MeProfile> {
  const response = await fetch("/core-api/me", {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(getAccessToken),
    },
    signal,
  });
  if (!response.ok) {
    throw new Error(`core-api/me ${response.status}`);
  }
  const payload = (await response.json()) as { id?: unknown; name?: unknown };
  return {
    id: typeof payload.id === "string" ? payload.id : "",
    name: typeof payload.name === "string" ? payload.name : "",
  };
}
