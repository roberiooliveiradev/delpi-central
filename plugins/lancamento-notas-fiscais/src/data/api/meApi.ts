import { httpGet } from "./httpClient";

export type MeProfile = {
  id: string;
  name: string;
  email: string;
  permissions: string[];
  is_superadmin?: boolean;
};

export async function fetchMeProfile(): Promise<MeProfile> {
  return httpGet<MeProfile>("/core-api/me");
}
