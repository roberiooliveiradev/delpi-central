import { httpGet } from "./httpClient";

export type MeProfile = {
  id: string;
  name: string;
  email: string;
};

export async function fetchMeProfile(signal?: AbortSignal): Promise<MeProfile> {
  return httpGet<MeProfile>("/core-api/me", { signal });
}

export function firstNameFromDisplay(name: string | null | undefined): string | null {
  const trimmed = (name ?? "").trim();
  if (!trimmed) return null;
  return trimmed.split(/\s+/)[0] || trimmed;
}
