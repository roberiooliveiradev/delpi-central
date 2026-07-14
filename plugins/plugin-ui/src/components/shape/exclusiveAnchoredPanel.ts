/**
 * Garante um AnchoredPanelPortal “peer” aberto por vez.
 * Abrir um novo fecha o anterior via `dismiss`.
 * Popovers aninhados (não exclusivos) passam `exclusive={false}`.
 */

export type ExclusiveAnchoredDismiss = () => void;

type ExclusiveEntry = {
  id: symbol;
  dismiss: ExclusiveAnchoredDismiss;
};

let activeExclusive: ExclusiveEntry | null = null;

export function claimExclusiveAnchoredPanel(
  id: symbol,
  dismiss: ExclusiveAnchoredDismiss,
): void {
  if (activeExclusive && activeExclusive.id !== id) {
    const previous = activeExclusive;
    activeExclusive = { id, dismiss };
    previous.dismiss();
    return;
  }
  activeExclusive = { id, dismiss };
}

export function releaseExclusiveAnchoredPanel(id: symbol): void {
  if (activeExclusive?.id === id) {
    activeExclusive = null;
  }
}

/** Só para testes — reseta o registro entre casos. */
export function resetExclusiveAnchoredPanelForTests(): void {
  activeExclusive = null;
}

/** Só para testes. */
export function peekExclusiveAnchoredPanelIdForTests(): symbol | null {
  return activeExclusive?.id ?? null;
}
