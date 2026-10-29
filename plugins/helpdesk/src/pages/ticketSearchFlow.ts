/**
 * Ticket list search flow helpers — debounce + stale-response guard.
 *
 * All searching/filtering happens in the Helpdesk BFF/GLPI; the frontend only
 * triggers queries and renders returned items. These helpers own the two
 * client-side concerns that must be correct for that contract:
 *
 * - `createDebouncer`: typing schedules a backend commit after a quiet
 *   period; Enter/clear paths can cancel or flush it explicitly.
 * - `createStaleGuard`: monotonically increasing request sequence — a
 *   delayed response from an older request can never overwrite newer state.
 */

export const SEARCH_DEBOUNCE_MS = 350;

export interface Debouncer {
  schedule(task: () => void): void;
  cancel(): void;
  pending(): boolean;
}

export function createDebouncer(debounceMs: number = SEARCH_DEBOUNCE_MS): Debouncer {
  let handle: ReturnType<typeof setTimeout> | undefined;
  return {
    schedule(task) {
      if (handle !== undefined) clearTimeout(handle);
      handle = setTimeout(() => {
        handle = undefined;
        task();
      }, debounceMs);
    },
    cancel() {
      if (handle !== undefined) clearTimeout(handle);
      handle = undefined;
    },
    pending() {
      return handle !== undefined;
    },
  };
}

export interface StaleGuard {
  /** Begin a new request; returns its sequence token. */
  next(): number;
  /** True when the token still belongs to the newest request. */
  isCurrent(seq: number): boolean;
}

export function createStaleGuard(): StaleGuard {
  let seq = 0;
  return {
    next() {
      return ++seq;
    },
    isCurrent(value: number) {
      return value === seq;
    },
  };
}
