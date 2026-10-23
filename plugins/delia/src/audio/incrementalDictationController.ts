/**
 * VD-F06 incremental dictation controller — orchestrates one bounded
 * dictation.incremental.v1 session against real captured PCM segments.
 *
 * Owns: session lifecycle, segment ids/sequences, capture ↔ transport
 * wiring, and application of real STT events to the draft through the
 * DictationSegmentReconciler. Owns nothing else: no React, no DOM, no
 * provider vocabulary beyond the injected transport seams.
 *
 * Injected seams keep the controller fully testable and honest:
 * - `capture`: real PCM source (AudioWorklet in production); segments
 *   are delivered as finished WAV blobs.
 * - `transport`: the dictationClient incremental functions.
 * - `anchors`: live caret/selection read from the composer textarea —
 *   the only authority for where the next segment lands.
 * - `draft`: get/set of the current draft text (host state).
 *
 * Every mutation of the draft goes through the reconciler: STT events
 * via applyRevision, human edits via noteUserEdit. Submit is never
 * invoked from here — transcripts are untrusted editable input only.
 */

import type {
  DeliaDictationSession,
  DeliaIncrementalEvent,
} from "../api/dictationClient";
import { DictationSegmentReconciler } from "./dictationSegmentReconciler";

export type IncrementalDictationState =
  | "idle"
  | "requesting_permission"
  | "listening"
  | "paused"
  | "finalizing"
  | "review"
  | "recoverable_error"
  | "unavailable";

export type IncrementalCapture = {
  /** Begin PCM capture; emits onSegment each time a slice is ready. */
  start(onSegment: (blob: Blob, durationMs: number) => void): Promise<void>;
  pause(): void;
  resume(): void;
  /** Stop capture and emit the trailing partial segment if any. */
  stop(): void;
  /** Stop capture without emitting the trailing segment (cancel). */
  abort(): void;
};

export type IncrementalTransport = {
  openSession(signal: AbortSignal): Promise<DeliaDictationSession>;
  streamSegment(
    input: {
      sessionId: string;
      segmentId: string;
      sequence: number;
      blob: Blob;
      mimeType: string;
      durationMs: number;
    },
    signal: AbortSignal,
  ): AsyncGenerator<DeliaIncrementalEvent>;
  endSession(sessionId: string, signal: AbortSignal): Promise<void>;
};

export type IncrementalDictationHooks = {
  /** Live caret/selection from the editable draft surface. */
  getAnchor(): { start: number; end: number };
  getDraft(): string;
  /** Apply the reconciler-produced draft; host owns the textarea caret. */
  setDraft(text: string): void;
  /** Human edit registration — every user keystroke routes here first. */
  noteUserEdit(prev: string, next: string): void;
  onStateChange(state: IncrementalDictationState): void;
  onError(message: string | null): void;
  /** Latest provisional text for the honest status strip (may be ""). */
  onProvisional(segmentId: string | null, text: string): void;
  /**
   * Advance the caret after an STT write — only ever called when the
   * caret sat exactly at the insert point, so it follows the text like
   * real typing. User carets elsewhere are never moved (doc-123 §5).
   */
  setCaret?(position: number): void;
};

export type IncrementalDictationControllerOptions = {
  capture: IncrementalCapture;
  transport: IncrementalTransport;
  hooks: IncrementalDictationHooks;
  /** Hard session bound from the admitted contract (ms). */
  maxSessionMs?: number | null;
  /** Max segments from the admitted contract. */
  maxSegments?: number | null;
  now?: () => number;
  /** Test seam: auto-finalize at the session bound instead of erroring. */
  autoFinalizeAtLimit?: boolean;
};

export class IncrementalDictationController {
  private readonly capture: IncrementalCapture;
  private readonly transport: IncrementalTransport;
  private readonly hooks: IncrementalDictationHooks;
  private readonly maxSessionMs: number | null;
  private readonly maxSegments: number | null;
  private readonly now: () => number;
  private readonly autoFinalize: boolean;

  private state: IncrementalDictationState = "idle";
  private sessionId: string | null = null;
  private reconciler: DictationSegmentReconciler | null = null;
  private abort: AbortController | null = null;
  private sequence = 0;
  private startedAt = 0;
  private paused = false;
  private finishing = false;
  private readonly inFlight = new Set<Promise<void>>();
  private lastDraft = "";

  constructor(options: IncrementalDictationControllerOptions) {
    this.capture = options.capture;
    this.transport = options.transport;
    this.hooks = options.hooks;
    this.maxSessionMs = options.maxSessionMs ?? null;
    this.maxSegments = options.maxSegments ?? null;
    this.now = options.now ?? Date.now;
    this.autoFinalize = options.autoFinalizeAtLimit ?? false;
  }

  getState(): IncrementalDictationState {
    return this.state;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  private setState(state: IncrementalDictationState): void {
    this.state = state;
    this.hooks.onStateChange(state);
  }

  /** Start an admitted incremental session: open → capture → stream. */
  async start(): Promise<void> {
    if (this.state !== "idle" && this.state !== "review") return;
    this.finishing = false;
    this.paused = false;
    this.sequence = 0;
    this.inFlight.clear();
    this.abort = new AbortController();
    const epoch = this.abort;
    this.lastDraft = this.hooks.getDraft();
    this.setState("requesting_permission");
    this.hooks.onError(null);
    try {
      const session = await this.transport.openSession(epoch.signal);
      if (epoch.signal.aborted) return;
      this.sessionId = session.sessionId;
      this.reconciler = new DictationSegmentReconciler(session.sessionId);
      this.startedAt = this.now();
      await this.capture.start((blob, durationMs) =>
        this.handleSegment(blob, durationMs),
      );
      if (epoch.signal.aborted) return;
      this.setState("listening");
    } catch (error) {
      if (epoch.signal.aborted) return;
      this.capture.abort();
      this.sessionId = null;
      this.reconciler = null;
      this.setState("recoverable_error");
      this.hooks.onError(errorMessage(error));
    }
  }

  /**
   * Human edits while listening must flow through here (before or with
   * the host setDraft). prev/next come straight from the textarea
   * onChange pair — the only authority for what the user actually did.
   */
  noteUserEdit(prev: string, next: string): void {
    this.lastDraft = next;
    this.reconciler?.noteUserEdit(prev, next);
  }

  pause(): void {
    if (this.state !== "listening") return;
    this.paused = true;
    this.capture.pause();
    this.setState("paused");
  }

  resume(): void {
    if (this.state !== "paused") return;
    this.paused = false;
    this.capture.resume();
    this.setState("listening");
  }

  /** Finalize: stop capture, flush trailing segment, await finals. */
  async finalize(): Promise<void> {
    if (this.state !== "listening" && this.state !== "paused") return;
    if (this.finishing) return; // idempotent — double-click is a no-op
    this.finishing = true;
    this.paused = false;
    this.setState("finalizing");
    this.capture.stop();
    await Promise.allSettled([...this.inFlight]);
    const sessionId = this.sessionId;
    if (sessionId) {
      const signal = this.abort?.signal;
      if (signal) await this.transport.endSession(sessionId, signal);
    }
    this.sessionId = null;
    this.reconciler = null;
    this.finishing = false;
    this.hooks.onProvisional(null, "");
    this.setState("review");
  }

  /**
   * Cancel: abort every in-flight stream and remove only the text still
   * owned by unfinished segments — confirmed text and human edits stay
   * (doc-123 case E). Remote processing may continue; the local wait
   * stops honestly.
   */
  cancel(): void {
    if (this.state === "idle" || this.state === "review") return;
    this.finishing = false;
    this.paused = false;
    this.abort?.abort();
    this.abort = null;
    this.capture.abort();
    const sessionId = this.sessionId;
    if (sessionId) {
      // Best-effort remote cleanup with a fresh signal — the session
      // abort above must not cancel this call too.
      void this.transport
        .endSession(sessionId, new AbortController().signal)
        .catch(() => undefined);
    }
    if (this.reconciler) {
      const trimmed = this.reconciler.cancelSession(this.hooks.getDraft());
      if (trimmed.text !== this.hooks.getDraft()) {
        this.hooks.setDraft(trimmed.text);
        this.lastDraft = trimmed.text;
      }
    }
    this.sessionId = null;
    this.reconciler = null;
    this.inFlight.clear();
    this.hooks.onProvisional(null, "");
    this.setState("idle");
  }

  /** Unmount/reload safety: same as cancel but silent. */
  dispose(): void {
    this.abort?.abort();
    this.abort = null;
    try {
      this.capture.abort();
    } catch {
      /* capture already closed */
    }
    this.sessionId = null;
    this.reconciler = null;
    this.state = "idle";
  }

  private sessionExpired(): boolean {
    return (
      this.maxSessionMs != null &&
      this.now() - this.startedAt > this.maxSessionMs
    );
  }

  private handleSegment(blob: Blob, durationMs: number): void {
    const sessionId = this.sessionId;
    const reconciler = this.reconciler;
    const abort = this.abort;
    if (!sessionId || !reconciler || !abort || abort.signal.aborted) return;
    if (this.maxSegments != null && this.sequence >= this.maxSegments) {
      this.hooks.onError(
        "Limite de segmentos do ditado atingido; finalize a captura.",
      );
      return;
    }
    if (this.sessionExpired()) {
      if (this.autoFinalize) {
        void this.finalize();
      } else {
        this.hooks.onError(
          "Tempo máximo do ditado atingido; finalize a captura.",
        );
      }
      return;
    }
    this.sequence += 1;
    const sequence = this.sequence;
    const segmentId = `seg-${sequence}`;
    const anchor = this.hooks.getAnchor();
    const draft = this.hooks.getDraft();
    this.lastDraft = draft;
    reconciler.beginSegment({
      sessionId,
      segmentId,
      sequence,
      anchorStart: Math.min(anchor.start, draft.length),
      anchorEnd: Math.min(anchor.end, draft.length),
    });
    const run = this.consumeSegment(
      sessionId,
      segmentId,
      sequence,
      blob,
      durationMs,
      abort.signal,
    );
    this.inFlight.add(run);
    void run.finally(() => this.inFlight.delete(run));
  }

  private async consumeSegment(
    sessionId: string,
    segmentId: string,
    sequence: number,
    blob: Blob,
    durationMs: number,
    signal: AbortSignal,
  ): Promise<void> {
    try {
      for await (const event of this.transport.streamSegment(
        {
          sessionId,
          segmentId,
          sequence,
          blob,
          mimeType: "audio/wav",
          durationMs,
        },
        signal,
      )) {
        if (signal.aborted || event.sessionId !== sessionId) continue;
        this.applyEvent(segmentId, event);
      }
    } catch (error) {
      if (signal.aborted) return;
      // A failed segment is honest state, never fabricated text. The
      // draft keeps whatever the segment already contributed.
      this.setState("recoverable_error");
      this.hooks.onError(errorMessage(error));
    }
  }

  private applyEvent(segmentId: string, event: DeliaIncrementalEvent): void {
    const reconciler = this.reconciler;
    if (!reconciler) return;
    if (event.type === "started") return;
    if (event.type === "error") {
      this.setState("recoverable_error");
      this.hooks.onError(
        `Falha na transcrição do trecho (${event.code ?? "error"}).`,
      );
      return;
    }
    if (event.type !== "partial" && event.type !== "final") return;
    const isFinal = event.type === "final" || event.isFinal === true;
    const draft = this.hooks.getDraft();
    const anchor = this.hooks.getAnchor();
    const result = reconciler.applyRevision(
      draft,
      segmentId,
      event.revision,
      event.text ?? "",
      isFinal,
    );
    if (!result.applied) return;
    this.hooks.setDraft(result.text);
    this.lastDraft = result.text;
    // Caret-follow rule: the caret only advances when it was collapsed
    // exactly at the insert point — the user "keeps typing" with STT.
    if (
      result.range &&
      this.hooks.setCaret &&
      anchor.start === anchor.end &&
      anchor.start === result.range.start
    ) {
      this.hooks.setCaret(result.range.end);
    }
    this.hooks.onProvisional(
      isFinal ? null : segmentId,
      isFinal ? "" : event.text ?? "",
    );
  }
}

function errorMessage(error: unknown): string {
  const code =
    error instanceof Error && "code" in error
      ? String((error as { code: unknown }).code)
      : "";
  switch (code) {
    case "forbidden":
    case "unauthenticated":
      return "Você não tem permissão para transcrever áudio. Você pode digitar a mensagem.";
    case "rate_limited":
      return "Muitas transcrições em sequência. Aguarde um instante e tente ditar novamente.";
    case "provider_timeout":
      return "A transcrição demorou demais. Tente ditar novamente ou digite a mensagem.";
    case "transcription_unavailable":
    case "provider_unavailable":
    case "network_error":
      return "A transcrição de voz está indisponível no momento. Você pode digitar a mensagem.";
    case "invalid_sequence":
      return "A sequência do ditado saiu de sincronia. Finalize e tente novamente.";
    case "session_not_found":
    case "session_expired":
      return "A sessão de ditado expirou. Finalize e tente novamente.";
    case "payload_too_large":
    case "duration_exceeded":
      return "Um trecho de áudio excede o limite permitido. Dite trechos menores.";
    default:
      return "Falha na transcrição ao vivo. Você pode continuar digitando ou tentar novamente.";
  }
}
