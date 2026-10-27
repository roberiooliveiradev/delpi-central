/** Cliente da BFF — perfil de participantes vinculados ao documento
 * (UX-009-RW01, Plano 113 §23.6).
 *
 * Contrato contextual (isolamento por documento+competência):
 * `POST|GET /closing/competences/{period}/documents/{document_id}/
 * participants*`. A BFF só resolve nomes/fotos de participantes com
 * vínculo canônico ao documento autorizado — ids sem vínculo são
 * omitidos da resposta (sem enumeração) e a foto de participante fora
 * do escopo retorna o mesmo 404 de recurso inexistente.
 *
 * `display_name = null` e 404 na foto são estados legítimos — a UI cai
 * em fallback neutro (iniciais), nunca em UUID nem foto inventada.
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

/** Contexto documental obrigatório — direito de acesso depende dele. */
export type ParticipantContext = {
  period: string;
  documentId: string;
};

function contextBasePath(ctx: ParticipantContext): string {
  return (
    `/closing/competences/${encodeURIComponent(ctx.period)}` +
    `/documents/${encodeURIComponent(ctx.documentId)}/participants`
  );
}

/** Lookup em lote (máx. 50) — só participantes vinculados retornam. */
export async function lookupParticipants(
  context: ParticipantContext,
  ids: readonly string[],
  options?: { signal?: AbortSignal },
): Promise<ParticipantLookupResult> {
  const unique = [...new Set(ids.map((id) => id.trim()).filter(Boolean))];
  if (!unique.length) return { items: [] };
  const envelope = await httpPost<Envelope<ParticipantLookupResult>>(
    cfApiUrl(`${contextBasePath(context)}/lookup`),
    { ids: unique.slice(0, 50) },
    { signal: options?.signal },
  );
  return envelope?.data ?? { items: [] };
}

/** Foto do participante vinculado — blob autenticado (404 = sem foto
 * publicada OU participante fora do vínculo documental). */
export async function downloadParticipantAvatar(
  context: ParticipantContext,
  userId: string,
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  return httpGetBlob(
    cfApiUrl(
      `${contextBasePath(context)}/${encodeURIComponent(userId)}/avatar`,
    ),
    options,
  );
}
