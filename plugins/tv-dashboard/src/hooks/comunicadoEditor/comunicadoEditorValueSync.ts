/**
 * Decide se o prop `value` externo deve substituir o config local do editor.
 * Evita o salto de frames no drag: o pai re-renderiza com nativeConfig stale
 * (save debounced) e o sync antigo reaplicava a posição antiga mid-gesture.
 *
 * Undo/redo do deck: passe `forceAccept` (via `historyEpoch`) — o fingerprint
 * restaurado parece “eco stale” frente ao último emit pós-edição.
 */
export function shouldAcceptExternalComunicadoValue(params: {
  identityChanged: boolean;
  incomingFingerprint: string;
  lastEmittedFingerprint: string | null;
  currentFingerprint: string;
  forceAccept?: boolean;
}): boolean {
  const {
    identityChanged,
    incomingFingerprint,
    lastEmittedFingerprint,
    currentFingerprint,
    forceAccept = false,
  } = params;

  if (forceAccept) return true;
  if (identityChanged) return true;
  if (incomingFingerprint === currentFingerprint) return false;
  if (lastEmittedFingerprint != null && incomingFingerprint !== lastEmittedFingerprint) {
    // Pai ainda não alcançou o último emit — valor externo é eco stale.
    return false;
  }
  if (incomingFingerprint === lastEmittedFingerprint) return false;
  return true;
}

/**
 * Edição colaborativa: mudança vinda de outro editor (WS `slide_draft` /
 * `presentation_updated`) chega com fingerprint diferente do último emit local
 * e seria rejeitada como «eco stale». O bump de `remoteRevision` marca o valor
 * externo como remoto legítimo — aceita, exceto quando idêntico ao atual
 * (evita reset de gesto/seleção sem mudança real).
 */
export function shouldForceAcceptRemoteComunicadoValue(params: {
  remoteRevisionChanged: boolean;
  incomingFingerprint: string;
  currentFingerprint: string;
}): boolean {
  return (
    params.remoteRevisionChanged && params.incomingFingerprint !== params.currentFingerprint
  );
}

export function fingerprintComunicadoValue(value: Record<string, unknown>): string {
  return JSON.stringify(value);
}
