/** Avatar do usuário — fonte canônica é a Core API
 * (`/me/person-profile` + `/me/person-profile/photo`), mesmo contrato
 * que o Comercial consome via proxy da commercial-api. Aqui o MFE lê
 * diretamente o owner com o Bearer humano do host; falhas degradam
 * para iniciais sem quebrar a Top Bar. */

import { getBlob, getJson } from "./httpClient";

const PROFILE_PATH = "/core-api/me/person-profile";
const PHOTO_PATH = "/core-api/me/person-profile/photo";

export type PersonProfile = {
  user_id?: string;
  job_title?: string | null;
  has_photo?: boolean;
  photo_url?: string | null;
};

export async function getMyPersonProfile(
  signal?: AbortSignal,
): Promise<PersonProfile> {
  return getJson<PersonProfile>(PROFILE_PATH, signal);
}

export async function getMyPersonProfilePhoto(
  signal?: AbortSignal,
): Promise<Blob> {
  return getBlob(PHOTO_PATH, signal);
}
