/** Core person-profile — owner is core-api, not helpdesk-api. */

export type PersonProfile = {
  has_photo: boolean;
};

export const PERSON_PROFILE_PATH = "/core-api/me/person-profile";
export const PERSON_PROFILE_PHOTO_PATH = "/core-api/me/person-profile/photo";

type TokenGetter = () => string | undefined;

let accessTokenGetter: TokenGetter | null = null;

export function configurePersonProfileClient(getAccessToken: TokenGetter) {
  accessTokenGetter = getAccessToken;
}

function headers(accept: string): Record<string, string> {
  const result: Record<string, string> = {
    Accept: accept,
    "X-Delpi-Caller-App": "helpdesk",
  };
  const token = accessTokenGetter?.();
  if (token) result.Authorization = `Bearer ${token}`;
  return result;
}

export async function getMyPersonProfile(signal?: AbortSignal): Promise<PersonProfile> {
  const response = await fetch(PERSON_PROFILE_PATH, {
    signal,
    headers: headers("application/json"),
  });
  if (!response.ok) throw new Error("person_profile_unavailable");
  return (await response.json()) as PersonProfile;
}

export async function getMyPersonProfilePhotoBlob(signal?: AbortSignal): Promise<Blob> {
  const response = await fetch(PERSON_PROFILE_PHOTO_PATH, {
    signal,
    headers: headers("application/octet-stream"),
  });
  if (!response.ok) throw new Error("person_profile_photo_unavailable");
  return response.blob();
}
