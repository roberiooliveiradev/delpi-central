import { firstNameFromDisplay } from "@delpi/plugin-ui/index";

import { httpGet } from "./httpClient";

export { firstNameFromDisplay };

export type MeProfile = {
  id: string;
  name: string;
  email: string;
};

export async function fetchMeProfile(signal?: AbortSignal): Promise<MeProfile> {
  return httpGet<MeProfile>("/core-api/me", { signal });
}

