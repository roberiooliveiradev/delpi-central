/**
 * useIncrementalDictation — React binding between the VD-F06
 * IncrementalDictationController and the live composer surface.
 *
 * The hook owns one controller instance per mount, wires its hooks to
 * the real textarea (caret/selection reads and writes) and to the
 * controlled draft (host value/onChange), and exposes the honest state
 * the UI renders: machine state, real RMS levels, elapsed time,
 * provisional text for the status strip, and typed errors.
 *
 * Human edits MUST route through noteUserEdit — DeliaComposer calls it
 * from the textarea onChange path before propagating. Controller-orig
 * writes are flagged so the host never double-registers them.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { createSegmentedPcmCapture } from "@delpi/plugin-ui/index";
import {
  IncrementalDictationController,
  type IncrementalDictationState,
  type IncrementalTransport,
} from "./incrementalDictationController";

export type UseIncrementalDictationOptions = {
  transport: IncrementalTransport;
  inputId: string;
  getDraft: () => string;
  setDraft: (text: string) => void;
  maxSessionMs?: number | null;
  maxSegments?: number | null;
};

export type IncrementalDictationUi = {
  state: IncrementalDictationState;
  active: boolean;
  levels: number[];
  elapsedMs: number;
  provisionalText: string;
  error: string | null;
  /** Marks controller-originated draft writes (not human edits). */
  isInternalWrite: () => boolean;
  noteUserEdit: (prev: string, next: string) => void;
  start: () => void;
  pause: () => void;
  resume: () => void;
  finalize: () => void;
  cancel: () => void;
};

const LEVEL_BARS = 24;

export function useIncrementalDictation(
  options: UseIncrementalDictationOptions,
): IncrementalDictationUi {
  const [state, setState] = useState<IncrementalDictationState>("idle");
  const [levels, setLevels] = useState<number[]>(() =>
    Array(LEVEL_BARS).fill(0.08),
  );
  const [elapsedMs, setElapsedMs] = useState(0);
  const [provisional, setProvisional] = useState<{
    id: string | null;
    text: string;
  }>({ id: null, text: "" });
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<IncrementalDictationController | null>(null);
  const internalWriteRef = useRef(false);
  const startedAtRef = useRef(0);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  if (controllerRef.current === null) {
    const capture = createSegmentedPcmCapture({
      onLevel: (level) =>
        setLevels((prev) => {
          const next = prev.slice(1);
          next.push(level);
          return next;
        }),
    });
    controllerRef.current = new IncrementalDictationController({
      capture,
      transport: options.transport,
      maxSessionMs: options.maxSessionMs ?? null,
      maxSegments: options.maxSegments ?? null,
      hooks: {
        getAnchor: () => {
          const el = document.getElementById(
            optionsRef.current.inputId,
          );
          if (el instanceof HTMLTextAreaElement) {
            return { start: el.selectionStart, end: el.selectionEnd };
          }
          const len = optionsRef.current.getDraft().length;
          return { start: len, end: len };
        },
        getDraft: () => optionsRef.current.getDraft(),
        setDraft: (text) => {
          internalWriteRef.current = true;
          optionsRef.current.setDraft(text);
        },
        noteUserEdit: () => undefined,
        onStateChange: (next) => {
          setState(next);
          if (next === "listening") startedAtRef.current = Date.now();
        },
        onError: (message) => setError(message),
        onProvisional: (id, text) => setProvisional({ id, text }),
        setCaret: (position) => {
          const el = document.getElementById(
            optionsRef.current.inputId,
          );
          if (el instanceof HTMLTextAreaElement) {
            el.setSelectionRange(position, position);
          }
        },
      },
    });
  }

  // Honest session timer — ticks only while capture is live.
  useEffect(() => {
    if (state !== "listening" && state !== "paused") return;
    const timer = window.setInterval(() => {
      setElapsedMs(Date.now() - startedAtRef.current);
    }, 500);
    return () => window.clearInterval(timer);
  }, [state]);

  // Unmount → invalidate everything (late events must die with it).
  useEffect(() => {
    const controller = controllerRef.current;
    return () => controller?.dispose();
  }, []);

  const start = useCallback(() => {
    setElapsedMs(0);
    setLevels(Array(LEVEL_BARS).fill(0.08));
    void controllerRef.current?.start();
  }, []);

  const isInternalWrite = useCallback(() => {
    const internal = internalWriteRef.current;
    internalWriteRef.current = false;
    return internal;
  }, []);

  return {
    state,
    active:
      state === "requesting_permission" ||
      state === "listening" ||
      state === "paused" ||
      state === "finalizing",
    levels,
    elapsedMs,
    provisionalText: provisional.text,
    error,
    isInternalWrite,
    noteUserEdit: (prev, next) =>
      controllerRef.current?.noteUserEdit(prev, next),
    start,
    pause: () => controllerRef.current?.pause(),
    resume: () => controllerRef.current?.resume(),
    finalize: () => void controllerRef.current?.finalize(),
    cancel: () => controllerRef.current?.cancel(),
  };
}
