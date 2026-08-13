import type { CommercialPresenceUpdatedEvent } from "../constants/realtime";

type PresenceHandler = (event: CommercialPresenceUpdatedEvent) => void;

/** Guarda o snapshot e notifica assinantes ativos. */
export function fanPresenceUpdated(
  lastPresenceRef: { current: CommercialPresenceUpdatedEvent | null },
  handlers: Set<PresenceHandler>,
  event: CommercialPresenceUpdatedEvent,
): void {
  lastPresenceRef.current = event;
  for (const handler of handlers) {
    handler(event);
  }
}

/**
 * Inscreve handler e, se já houver snapshot (late subscriber), faz replay imediato.
 */
export function subscribePresenceWithReplay(
  lastPresenceRef: { current: CommercialPresenceUpdatedEvent | null },
  handlers: Set<PresenceHandler>,
  handler: PresenceHandler,
): () => void {
  handlers.add(handler);
  const snapshot = lastPresenceRef.current;
  if (snapshot) {
    handler(snapshot);
  }
  return () => {
    handlers.delete(handler);
  };
}
