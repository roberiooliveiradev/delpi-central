import { httpGet, httpGetBlob } from "./httpClient";

/** Core person-profile (global identity) — owner is core-api, not supplies-api. */
export type PersonProfile = {
  user_id: string;
  job_title: string | null;
  phone_e164: string | null;
  mobile_e164: string | null;
  whatsapp_e164: string | null;
  has_photo: boolean;
  photo_url: string | null;
  updated_at: string | null;
};

const PERSON_PROFILE_PATH = "/core-api/me/person-profile";
const PERSON_PROFILE_PHOTO_PATH = "/core-api/me/person-profile/photo";

export function getMyPersonProfile(signal?: AbortSignal): Promise<PersonProfile> {
  return httpGet<PersonProfile>(PERSON_PROFILE_PATH, { signal });
}

export function getMyPersonProfilePhotoBlob(signal?: AbortSignal): Promise<Blob> {
  return httpGetBlob(PERSON_PROFILE_PHOTO_PATH, { signal });
}
