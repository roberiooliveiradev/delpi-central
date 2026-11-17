/** Avatar de participantes (atores do histórico/conversação) — BFF
 * governado da engineering-api (`/v1/participants/*`) que proxeia a
 * fonte canônica do Portal (Core person-profile via S2S). Falhas
 * degradam para iniciais; nunca exibimos GUID como foto. */

import { getBlob } from "./httpClient";

const BASE = "/apps/engineering-api/v1/participants";

export async function downloadParticipantAvatarBlob(
  userId: string,
  signal?: AbortSignal,
): Promise<Blob> {
  return getBlob(`${BASE}/${encodeURIComponent(userId)}/avatar`, signal);
}
