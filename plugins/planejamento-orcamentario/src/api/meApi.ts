import { httpGet } from "./httpClient";

export type MeProfile = {
  id: string;
  name: string;
  email: string;
  permissions: string[];
};

export async function fetchMeProfile(signal?: AbortSignal): Promise<MeProfile> {
  return httpGet<MeProfile>("/core-api/me", { signal });
}
