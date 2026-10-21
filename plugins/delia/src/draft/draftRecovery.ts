import { useCallback, useEffect, useRef, useState } from "react";

/**
 * DÉLIA — ConversationDraftRecovery (doc 102 §§4–5).
 *
 * Transient, in-memory-only recovery of the LAST explicitly cleared
 * draft in the current local UI session. The host owns the candidate
 * lifecycle: a snapshot is taken only by the explicit clear action,
 * the notice lives for `dismissMs` (pausable while the user hovers or
 * focuses it), and the candidate is discarded on expiry, new draft
 * text, send, request-mode change, conversation/epoch change, unmount
 * or reload — never persisted, never sent anywhere.
 *
 * The owner of presentation is plugin-ui (`EditorChromeNotice`); this
 * hook owns state/transitions only. `canRestore`/`epoch` are host
 * guards evaluated lazily at undo time so a stale callback can never
 * restore a draft into a different session state.
 */

/** Reference UX duration for the undo notice (spec §4.2 target). */
export const DRAFT_RECOVERY_DISMISS_MS = 8_000;

export type DraftRecoveryOptions = {
  /**
   * Host gate evaluated lazily: same epoch/conversation, idle request
   * mode, no in-flight request and a still-empty draft. Must return
   * the LIVE values (the hook reads the latest options each render).
   */
  canRestore: () => boolean;
  /**
   * Monotonic local epoch (e.g. a request/conversation counter). The
   * candidate records the epoch at capture time; undo compares it to
   * the live epoch so an older candidate cannot cross a boundary.
   */
  epoch: () => number;
  /** Restore callback — receives the exact snapshot text. */
  onRestore: (text: string) => void;
  /** Notice lifetime in ms; defaults to DRAFT_RECOVERY_DISMISS_MS. */
  dismissMs?: number;
};

export type DraftRecoveryHandle = {
  /** Whether the "Rascunho limpo — Desfazer" notice is on screen. */
  visible: boolean;
  /**
   * Snapshot the explicitly cleared draft and show the notice.
   * Replaces any prior candidate; empty/whitespace-only input is a
   * no-op (nothing worth recovering).
   */
  capture: (cleared: string) => void;
  /**
   * Undo intent — restores the snapshot only when every gate still
   * holds, consumes the candidate atomically (double-click safe) and
   * closes the notice. An invalid candidate is discarded instead.
   */
  undo: () => void;
  /** Discard the candidate and hide the notice (invalidation paths). */
  invalidate: () => void;
  /** Pause the expiry countdown (pointer/focus inside the notice). */
  pause: () => void;
  /** Resume the countdown with the remaining time. */
  resume: () => void;
};

type Candidate = { text: string; epoch: number };

export function useDraftRecovery(options: DraftRecoveryOptions): DraftRecoveryHandle {
  const optionsRef = useRef(options);
  optionsRef.current = options;
  const dismissMs = options.dismissMs ?? DRAFT_RECOVERY_DISMISS_MS;

  const [visible, setVisible] = useState(false);
  const candidateRef = useRef<Candidate | null>(null);
  const timerRef = useRef<number | null>(null);
  const remainingMsRef = useRef<number>(0);
  const expiresAtRef = useRef<number>(0);
  const pausedRef = useRef(false);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const invalidate = useCallback(() => {
    clearTimer();
    candidateRef.current = null;
    pausedRef.current = false;
    setVisible(false);
  }, [clearTimer]);

  const startTimer = useCallback(
    (ms: number) => {
      clearTimer();
      expiresAtRef.current = Date.now() + ms;
      timerRef.current = window.setTimeout(() => {
        timerRef.current = null;
        invalidate();
      }, ms);
    },
    [clearTimer, invalidate],
  );

  const capture = useCallback(
    (cleared: string) => {
      if (cleared.length === 0) return;
      candidateRef.current = { text: cleared, epoch: optionsRef.current.epoch() };
      pausedRef.current = false;
      remainingMsRef.current = dismissMs;
      setVisible(true);
      startTimer(dismissMs);
    },
    [dismissMs, startTimer],
  );

  const undo = useCallback(() => {
    const candidate = candidateRef.current;
    if (candidate === null) return;
    if (candidate.epoch !== optionsRef.current.epoch() ||
        !optionsRef.current.canRestore()) {
      invalidate();
      return;
    }
    // Consume first: a double-click or racing callback can never
    // restore the same snapshot twice.
    candidateRef.current = null;
    clearTimer();
    pausedRef.current = false;
    setVisible(false);
    optionsRef.current.onRestore(candidate.text);
  }, [clearTimer, invalidate]);

  const pause = useCallback(() => {
    if (pausedRef.current || timerRef.current === null) return;
    pausedRef.current = true;
    remainingMsRef.current = Math.max(0, expiresAtRef.current - Date.now());
    clearTimer();
  }, [clearTimer]);

  const resume = useCallback(() => {
    if (!pausedRef.current || candidateRef.current === null) return;
    pausedRef.current = false;
    startTimer(remainingMsRef.current);
  }, [startTimer]);

  // Unmount cancels every pending timer and drops the snapshot.
  useEffect(
    () => () => {
      clearTimer();
      candidateRef.current = null;
    },
    [clearTimer],
  );

  return { visible, capture, undo, invalidate, pause, resume };
}
