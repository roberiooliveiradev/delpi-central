/**
 * Decide se um `presentation_updated` pode dispensar o reload autoritativo.
 *
 * Contrato de supressão segura (VISTA-TV-024): só pular quando a revisão do
 * evento já está incorporada no estado local — commits próprios e de contextos
 * irmãos publicam o write-head no ack (`publishPlaylistWriteHead`), então uma
 * revisão de evento ≤ revisão rastreada (max(knownPlaylistRevision,
 * sharedWriteHead)) é redundância garantida.
 *
 * WS antes do ACK: revisão do evento == rastreada+1 com escrita própria em
 * voo é ambígua (pode ser o próprio commit ou uma escrita estrangeira que
 * tomou a revisão). Suprimir é seguro: se for estrangeira, o CAS do pendente
 * vira 409 e o caminho server-wins recarrega o estado autoritativo.
 *
 * Sem revisão no evento (payload antigo, reconexão, playlist removida):
 * sempre reload — `SAFE RELOAD > UNSAFE SUPPRESSION`.
 */
export function shouldSkipPresentationUpdatedReload(params: {
  /** playlistRevision do evento WS (pode ser ausente em payloads antigos). */
  eventRevision: number | null;
  /** max(knownPlaylistRevision, sharedWriteHead) — revisão já incorporada. */
  trackedRevision: number;
  /** Há escrita própria em voo na lane desta playlist. */
  hasPendingOwnWrite: boolean;
}): boolean {
  const { eventRevision, trackedRevision, hasPendingOwnWrite } = params;
  if (eventRevision == null || !Number.isFinite(eventRevision)) return false;
  if (eventRevision <= trackedRevision) return true;
  return hasPendingOwnWrite && eventRevision === trackedRevision + 1;
}
