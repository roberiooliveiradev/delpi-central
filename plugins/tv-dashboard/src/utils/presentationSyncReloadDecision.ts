/**
 * Decide se um `presentation_updated` pode dispensar o reload autoritativo.
 *
 * Contrato de supressão segura (VISTA-TV-024 / 024-R1): só pular quando a
 * revisão do evento já está incorporada no estado local — commits próprios e
 * de contextos irmãos publicam o write-head no ack (`publishPlaylistWriteHead`),
 * então uma revisão de evento ≤ revisão rastreada (max(knownPlaylistRevision,
 * sharedWriteHead)) é redundância garantida.
 *
 * WS antes do ACK: revisão do evento == rastreada+1 com escrita própria em
 * voo é ambígua (pode ser o próprio commit ou uma escrita estrangeira que
 * tomou a revisão). Não é prova de autoria — o evento é registrado como
 * `pendingAmbiguousSyncRevision` e reconciliado obrigatoriamente quando a
 * escrita termina (`onPlaylistWriteSettled`): ack cobrindo a revisão →
 * incorporado; rejeição/timeout/cancelamento com revisão ainda não coberta
 * → reload (a atualização remota nunca fica permanentemente ignorada).
 *
 * Sem revisão no evento (payload antigo, reconexão, playlist removida):
 * sempre reload — `SAFE RELOAD > UNSAFE SUPPRESSION`.
 */
export type PresentationSyncReloadDecision =
  | "reload"
  | "skip_incorporated"
  | "skip_ambiguous_pending";

export function resolvePresentationSyncReloadDecision(params: {
  /** playlistRevision do evento WS (pode ser ausente em payloads antigos). */
  eventRevision: number | null;
  /** max(knownPlaylistRevision, sharedWriteHead) — revisão já incorporada. */
  trackedRevision: number;
  /** Há escrita própria em voo na lane desta playlist. */
  hasPendingOwnWrite: boolean;
}): PresentationSyncReloadDecision {
  const { eventRevision, trackedRevision, hasPendingOwnWrite } = params;
  if (eventRevision == null || !Number.isFinite(eventRevision)) return "reload";
  if (eventRevision <= trackedRevision) return "skip_incorporated";
  if (hasPendingOwnWrite && eventRevision === trackedRevision + 1) {
    return "skip_ambiguous_pending";
  }
  return "reload";
}

/**
 * Decisão na conciliação diferida: a revisão ambígua registrada ainda está
 * acima do rastreado quando a escrita termina → recuperação obrigatória.
 */
export function shouldRecoverAmbiguousSyncEvent(params: {
  ambiguousRevision: number | null;
  trackedRevision: number;
}): boolean {
  const { ambiguousRevision, trackedRevision } = params;
  return ambiguousRevision != null && ambiguousRevision > trackedRevision;
}
