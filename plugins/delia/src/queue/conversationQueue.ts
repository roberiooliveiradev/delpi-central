import { useCallback, useRef, useState } from "react";

/**
 * Doc 71 + doc 122 §11 (F03-B) — ephemeral conversation queue.
 *
 * MEMORY-ONLY, scoped to the mounted conversation experience: items
 * live in React state, survive re-renders while the same instance is
 * mounted, and are honestly discarded on unmount/reload/surface swap
 * (full-page ↔ Dock are separate mounts — no persistence is invented
 * to bridge them). IDs are local manipulation handles only — never
 * backend authorities, never sent on the wire.
 *
 * `takeNext` consumes the head item synchronously against a ref: an
 * item is removed from the queue BEFORE its dispatch begins, so a
 * repeated effect run, Strict Mode double-invocation or a late render
 * can never hand the same item out twice. Text is captured at enqueue
 * time and cannot mutate while in flight.
 */
export type PendingConversationRequest = {
  /** Local UI handle only — opaque, never authoritative. */
  id: string;
  /** Exact text admitted by the user at enqueue time (frozen). */
  text: string;
  createdAt: number;
};

export type ConversationQueueController = {
  /** Pending items in dispatch order (head = next eligible). */
  items: readonly PendingConversationRequest[];
  /** Admit a new pending request at the tail. Returns the local id. */
  enqueue: (text: string) => PendingConversationRequest;
  /** Reorder a pending item one position. Never touches in-flight work. */
  moveItem: (itemId: string, direction: "up" | "down") => void;
  /** Drop a pending item. Never touches in-flight work. */
  removeItem: (itemId: string) => void;
  /**
   * Atomically consume the next eligible item (FIFO after reorders).
   * Returns null when empty. A consumed item is gone — the caller owns
   * its dispatch outcome.
   */
  takeNext: () => PendingConversationRequest | null;
  /** Discard all pendings (conversation reset/invalidation). */
  clear: () => void;
};

let localQueueSeq = 0;

function nextLocalId(): string {
  localQueueSeq += 1;
  return `local-queue-${localQueueSeq}`;
}

export function useConversationQueue(): ConversationQueueController {
  // Ref mirror is the atomic-consumption authority: state drives the
  // render, the ref guarantees takeNext can never yield an item twice
  // no matter how React schedules effects around the dispatch.
  const itemsRef = useRef<PendingConversationRequest[]>([]);
  const [items, setItems] = useState<readonly PendingConversationRequest[]>(
    [],
  );

  const commit = useCallback((next: PendingConversationRequest[]) => {
    itemsRef.current = next;
    setItems(next);
  }, []);

  const enqueue = useCallback(
    (text: string) => {
      const item: PendingConversationRequest = {
        id: nextLocalId(),
        text,
        createdAt: Date.now(),
      };
      commit([...itemsRef.current, item]);
      return item;
    },
    [commit],
  );

  const moveItem = useCallback(
    (itemId: string, direction: "up" | "down") => {
      const list = itemsRef.current;
      const index = list.findIndex((item) => item.id === itemId);
      if (index < 0) return;
      const target = direction === "up" ? index - 1 : index + 1;
      if (target < 0 || target >= list.length) return;
      const next = [...list];
      [next[index], next[target]] = [next[target], next[index]];
      commit(next);
    },
    [commit],
  );

  const removeItem = useCallback(
    (itemId: string) => {
      const list = itemsRef.current;
      const index = list.findIndex((item) => item.id === itemId);
      if (index < 0) return;
      commit(list.filter((item) => item.id !== itemId));
    },
    [commit],
  );

  const takeNext = useCallback(() => {
    const head = itemsRef.current[0];
    if (!head) return null;
    commit(itemsRef.current.slice(1));
    return head;
  }, [commit]);

  const clear = useCallback(() => {
    if (itemsRef.current.length === 0) return;
    commit([]);
  }, [commit]);

  return { items, enqueue, moveItem, removeItem, takeNext, clear };
}
