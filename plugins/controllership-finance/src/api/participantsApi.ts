/** Cliente da BFF — perfil de participantes (UX-009, Plano 113 §23.3).
 *
 * Contrato: `POST|GET /closing/participants*`. Nomes oficiais vêm do
 * diretório do Core (bearer do próprio usuário); fotos são proxy
 * read-through do person-profile Core (S2S). `display_name = null` e
 * 404 na foto são estados legítimos — a UI cai em fallback neutro
 * (iniciais), nunca em UUID nem foto inventada.
 */
import {
  cfApiUrl,
  httpGetBlob,
  httpPost,
} from "./httpClient";

type Envelope<T> = { data?: T };

export type ParticipantProfile = {
  user_id: string;
  display_name: string | null;
  has_photo: boolean;
};

export type ParticipantLookupResult = {
  items: ParticipantProfile[];
};

/** Lookup em lote (máx. 50) — nome oficial do diretório + flag de foto. */
export async function lookupParticipants(
  ids: readonly string[],
  options?: { signal?: AbortSignal },
): Promise<ParticipantLookupResult> {
  const unique = [...new Set(ids.map((id) => id.trim()).filter(Boolean))];
  if (!unique.length) return { items: [] };
  const envelope = await httpPost<Envelope<ParticipantLookupResult>>(
    cfApiUrl("/closing/participants/lookup"),
    { ids: unique.slice(0, 50) },
    { signal: options?.signal },
  );
  return envelope?.data ?? { items: [] };
}

/** Foto do participante — blob autenticado (404 = sem foto publicada). */
export async function downloadParticipantAvatar(
  userId: string,
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  return httpGetBlob(
    cfApiUrl(`/closing/participants/${encodeURIComponent(userId)}/avatar`),
    options,
  );
}
