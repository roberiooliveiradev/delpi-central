import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { MutableRefObject, ReactNode } from "react";
import {
  AudioRecorderControl,
  audioRecorderErrorMessage,
  formatAudioDurationMs,
  HelpTooltip,
  IconButton,
  MessageComposer,
} from "@delpi/plugin-ui/index";
import { Mic, Pause, Play, Square, Trash2, X } from "lucide-react";

import { INTERACTION_INPUT_CHAR_LIMIT } from "../api/interactionClient";
import {
  DELIA_DICTATION_STT_DISCLOSURE,
  DELIA_LOCAL_CAPTURE_DISCLOSURE,
} from "../audio/audioCaptureTestAdmission";
import type {
  DeliaDictationError,
  DeliaDictationTranscription,
} from "../api/dictationClient";
import { useIncrementalDictation } from "../audio/useIncrementalDictation";
import type { IncrementalTransport } from "../audio/incrementalDictationController";
import {
  DEFAULT_DICTATION_MODE,
  type DictationMode,
} from "../audio/dictationMode";
import { ComposerSettingsMenu } from "./ComposerSettingsMenu";
import { DictationModeSettings } from "./DictationModeSettings";
import type { LocalAudioDraft } from "@delpi/plugin-ui/index";

/** One completed local capture → untrusted editable text (VD-F03). */
export type DeliaDictationTranscriber = (
  draft: LocalAudioDraft,
  signal: AbortSignal,
) => Promise<DeliaDictationTranscription>;

export type DeliaComposerProps = {
  inputId: string;
  value: string;
  onChange: (value: string) => void;
  /** Explicit user intent only — never invoked programmatically. */
  onSubmit: () => void;
  /**
   * Doc 71 (F03-B) — enqueue intent while a turn is in flight. When
   * provided, the draft stays editable during in-flight and Enter/the
   * queue control admit text into the ephemeral conversation queue
   * instead of submitting. When omitted, in-flight locking is
   * unchanged.
   */
  onEnqueue?: () => void;
  loading?: boolean;
  requestMode?: "idle" | "responding_cancelable" | "responding_not_cancelable" | "stopping";
  onStop?: () => void;
  placeholder?: string;
  /**
   * Product admission for local audio capture UI.
   * Available to every legitimately admitted DÉLIA user (delia.access
   * enforced upstream). Does not enable upload, transcription, or
   * remote send.
   */
  audioCaptureEnabled?: boolean;
  /**
   * Approved max recording duration (ms). Required with maxBytes
   * when audioCaptureEnabled is true; otherwise the control stays unavailable.
   */
  audioCaptureMaxDurationMs?: number;
  /** Approved max recording size (bytes). See audioCaptureMaxDurationMs. */
  audioCaptureMaxBytes?: number;
  /**
   * dictation.transcription.v1 transcriber — present only when the
   * backend reports the capability available (GET /dictation/status).
   * Absent → capture stays in the honest local-preview mode: no
   * transcribing state, no fabricated text.
   */
  dictationTranscriber?: DeliaDictationTranscriber | null;
  /**
   * Draft recovery seam (doc 102): called with the CURRENT draft text
   * right before the explicit "Limpar rascunho" action clears it, so
   * the host can snapshot it for the transient undo affordance.
   * Optional — without it the button still clears as before.
   */
  onClearDraft?: (clearedValue: string) => void;
  /**
   * Transient undo affordance (doc 102 R1): render-only node injected
   * into the composer secondary-actions row — next to the dictation
   * trigger — only while a recovery candidate exists. Owned by the
   * host (plugins/delia); this component never inspects it.
   */
  draftRecoveryAction?: ReactNode;
  /**
   * VD-F06 dictation.incremental.v1 transport — present only when the
   * backend status reports `incremental.available` AND segmented PCM
   * capture is supported. When admitted, the mic trigger starts a real
   * progressive session (textarea stays editable); when absent the
   * VD-F03 one-shot path remains the honest fallback.
   */
  incrementalTransport?: IncrementalTransport | null;
  /** Admitted session bound from the contract (ms). */
  incrementalMaxSessionMs?: number | null;
  /** Admitted segment bound from the contract. */
  incrementalMaxSegments?: number | null;
  /**
   * Internal: composer settings menu node (dictation mode section) the
   * parent wires into the secondary-actions row. Never set by hosts.
   */
  composerSettingsAction?: ReactNode;
  /**
   * Internal: reports whether a capture/transcription is in progress so
   * the dictation-mode options can lock switching. Never set by hosts.
   */
  onCaptureActivityChange?: (busy: boolean) => void;
};

function dictationErrorMessage(error: unknown): string {
  const code =
    error instanceof Error && "code" in error
      ? String((error as DeliaDictationError).code)
      : "";
  switch (code) {
    case "unauthenticated":
    case "forbidden":
      return "Você não tem permissão para transcrever áudio. Você pode digitar a mensagem.";
    case "payload_too_large":
    case "duration_exceeded":
      return "O áudio excede o limite permitido. Dite um trecho menor ou digite a mensagem.";
    case "rate_limited":
      return "Muitas transcrições em sequência. Aguarde um instante e tente ditar novamente.";
    case "provider_timeout":
      return "A transcrição demorou demais. Tente ditar novamente ou digite a mensagem.";
    case "empty_transcription":
      return "Não foi possível reconhecer fala no áudio. Tente ditar novamente ou digite a mensagem.";
    case "unsupported_media":
    case "provider_rejected":
      return "Este formato de áudio não pôde ser transcrito. Digite a mensagem.";
    case "transcription_unavailable":
    case "provider_unavailable":
    case "network_error":
      return "A transcrição de voz está indisponível no momento. Você pode digitar a mensagem.";
    default:
      return "Falha ao transcrever o áudio. Tente ditar novamente ou digite a mensagem.";
  }
}

/**
 * VD-F05 draft merge: transcript replaces the snapshotted selection or
 * lands at the caret — never a silent append/overwrite. Boundary
 * whitespace is normalized so consecutive dictations don't glue words
 * and the composer character limit is enforced explicitly: an
 * overflowing merge is truncated and reported, never silently lost.
 */
function mergeTranscriptIntoDraft(
  value: string,
  start: number,
  end: number,
  insert: string,
  limit: number,
): { text: string; caret: number; truncated: boolean } {
  const left = value.slice(0, start);
  const right = value.slice(end);
  let chunk = insert;
  if (left.length > 0 && !/\s$/.test(left) && !/^\s/.test(chunk)) {
    chunk = ` ${chunk}`;
  }
  if (right.length > 0 && !/^\s/.test(right) && !/\s$/.test(chunk)) {
    chunk = `${chunk} `;
  }
  const merged = left + chunk + right;
  const truncated = merged.length > limit;
  const text = truncated ? merged.slice(0, limit) : merged;
  return { text, caret: Math.min(start + chunk.length, limit), truncated };
}

/**
 * DÉLIA composer — thin product wrapper over the plugin-ui
 * `MessageComposer` (single surface, write band + toolbar).
 *
 * Voice Dictation (VD-F02 + VD-F03): while capture or a real
 * transcription is active, the recorder/transcription panel occupies
 * the SAME composer surface (`MessageComposer.bodyOverride`) — the
 * textarea and the normal toolbar are not rendered, so no typing or
 * textual send is possible. The draft is untouched in host state.
 *
 * With an admitted `dictationTranscriber`, finishing a capture starts a
 * REAL `transcribing` state: the audio goes only to the dictation
 * contract (never multimodal analysis), the returned text is spliced
 * into the draft at the caret/selection snapshotted when dictation
 * began (never a silent append), and submit remains exclusively the
 * user's action. Without it, finishing yields the honest local preview.
 */
/**
 * Dual-mode dictation (PO decision 2026-10-23, spec 123 §12).
 *
 * The composer owns a mount-scoped `DictationMode` that always starts
 * at "batch" — incremental backend admission NEVER selects "live".
 * The user picks a mode before capture; switching is blocked while a
 * capture/transcription is active (each path reports its busy state
 * through `onCaptureActivityChange`). Draft text survives the switch;
 * the textarea caret/selection is snapshotted and restored across the
 * subtree remount the mode change implies.
 */
export function DeliaComposer({
  inputId,
  value,
  onChange,
  onSubmit,
  onEnqueue,
  loading = false,
  requestMode,
  onStop,
  placeholder = "Pergunte à DÉLIA…",
  audioCaptureEnabled = false,
  audioCaptureMaxDurationMs,
  audioCaptureMaxBytes,
  dictationTranscriber = null,
  onClearDraft,
  draftRecoveryAction,
  incrementalTransport = null,
  incrementalMaxSessionMs = null,
  incrementalMaxSegments = null,
}: DeliaComposerProps) {
  const [mode, setMode] = useState<DictationMode>(DEFAULT_DICTATION_MODE);
  const [captureBusy, setCaptureBusy] = useState(false);
  // Settings-menu open state lives here because switching batch ⇄ live
  // swaps the whole composer subtree and remounts the menu (spec 125 §10).
  const [settingsOpen, setSettingsOpen] = useState(false);
  const liveAvailable = incrementalTransport != null;
  const batchAvailable = audioCaptureEnabled && dictationTranscriber != null;
  const useLive = mode === "live" && liveAvailable;
  const showSettings = liveAvailable || batchAvailable || mode === "live";

  // Caret/selection survive the subtree remount a mode switch implies.
  const selectionRef: MutableRefObject<{
    start: number;
    end: number;
  } | null> = useRef(null);
  useEffect(() => {
    const track = () => {
      const el = document.getElementById(inputId);
      if (
        el instanceof HTMLTextAreaElement &&
        document.activeElement === el
      ) {
        selectionRef.current = {
          start: el.selectionStart,
          end: el.selectionEnd,
        };
      }
    };
    document.addEventListener("selectionchange", track);
    return () => document.removeEventListener("selectionchange", track);
  }, [inputId]);
  useLayoutEffect(() => {
    const sel = selectionRef.current;
    if (!sel) return;
    const el = document.getElementById(inputId);
    if (el instanceof HTMLTextAreaElement) {
      el.focus();
      el.setSelectionRange(
        Math.min(sel.start, el.value.length),
        Math.min(sel.end, el.value.length),
      );
    }
  }, [mode, inputId]);

  // Spec 125: the permanent mode strip is gone — the batch/live choice
  // lives inside the composer settings menu, a discreet toolbar control
  // whose options stay visible (but disabled) during capture.
  const settingsAction = showSettings ? (
    <ComposerSettingsMenu open={settingsOpen} onOpenChange={setSettingsOpen}>
      <DictationModeSettings
        value={mode}
        onChange={setMode}
        disabled={captureBusy}
        liveAvailable={liveAvailable}
      />
    </ComposerSettingsMenu>
  ) : null;

  return (
    <>
      {useLive && incrementalTransport ? (
        <DeliaComposerIncremental
          inputId={inputId}
          value={value}
          onChange={onChange}
          onSubmit={onSubmit}
          onEnqueue={onEnqueue}
          loading={loading}
          requestMode={requestMode}
          onStop={onStop}
          placeholder={placeholder}
          transport={incrementalTransport}
          maxSessionMs={incrementalMaxSessionMs}
          maxSegments={incrementalMaxSegments}
          onClearDraft={onClearDraft}
          draftRecoveryAction={draftRecoveryAction}
          composerSettingsAction={settingsAction}
          onCaptureActivityChange={setCaptureBusy}
        />
      ) : (
        <DeliaComposerBatch
          inputId={inputId}
          value={value}
          onChange={onChange}
          onSubmit={onSubmit}
          onEnqueue={onEnqueue}
          loading={loading}
          requestMode={requestMode}
          onStop={onStop}
          placeholder={placeholder}
          audioCaptureEnabled={audioCaptureEnabled}
          audioCaptureMaxDurationMs={audioCaptureMaxDurationMs}
          audioCaptureMaxBytes={audioCaptureMaxBytes}
          dictationTranscriber={dictationTranscriber}
          onClearDraft={onClearDraft}
          draftRecoveryAction={draftRecoveryAction}
          composerSettingsAction={settingsAction}
          onCaptureActivityChange={setCaptureBusy}
        />
      )}
    </>
  );
}

/** VD-F03 one-shot dictation path (existing modal capture + merge). */
function DeliaComposerBatch({
  inputId,
  value,
  onChange,
  onSubmit,
  onEnqueue,
  loading = false,
  requestMode,
  onStop,
  placeholder = "Pergunte à DÉLIA…",
  audioCaptureEnabled = false,
  audioCaptureMaxDurationMs,
  audioCaptureMaxBytes,
  dictationTranscriber = null,
  onClearDraft,
  draftRecoveryAction,
  composerSettingsAction,
  onCaptureActivityChange,
}: DeliaComposerProps) {
  const inFlight =
    loading || (requestMode != null && requestMode !== "idle");
  const [dictating, setDictating] = useState(false);
  const [dictationError, setDictationError] = useState<string | null>(null);
  const [transcribed, setTranscribed] = useState(false);
  const discardRef: MutableRefObject<(() => void) | null> = useRef(null);
  const selectionRef: MutableRefObject<{
    start: number;
    end: number;
  } | null> = useRef(null);
  const caretRef: MutableRefObject<number | null> = useRef(null);
  const sessionRef = useRef(0);
  const abortRef: MutableRefObject<AbortController | null> = useRef(null);
  const [recorderBlocking, setRecorderBlocking] = useState(false);
  const [previewPending, setPreviewPending] = useState(false);

  // Mode-switch lock: recording/stopping/preview/transcribing all keep
  // the dual-mode selector disabled until the flow settles.
  useEffect(() => {
    onCaptureActivityChange?.(recorderBlocking || dictating || previewPending);
  }, [recorderBlocking, dictating, previewPending, onCaptureActivityChange]);
  useEffect(
    () => () => onCaptureActivityChange?.(false),
    [onCaptureActivityChange],
  );

  // Track the textarea caret/selection so a transcript lands exactly
  // where the user was editing when dictation began (VD-07 rule).
  useEffect(() => {
    const track = () => {
      const el = document.getElementById(inputId);
      if (el instanceof HTMLTextAreaElement && document.activeElement === el) {
        selectionRef.current = {
          start: el.selectionStart,
          end: el.selectionEnd,
        };
      }
    };
    document.addEventListener("selectionchange", track);
    return () => document.removeEventListener("selectionchange", track);
  }, [inputId]);

  // Invalidate any in-flight transcription on unmount.
  useEffect(
    () => () => {
      sessionRef.current += 1;
      abortRef.current?.abort();
      abortRef.current = null;
    },
    [],
  );

  const handleDraftReady = (draft: LocalAudioDraft) => {
    setPreviewPending(true);
    if (!dictationTranscriber) return; // honest local preview
    discardRef.current?.();
    const session = (sessionRef.current += 1);
    const el = document.getElementById(inputId);
    const live =
      el instanceof HTMLTextAreaElement
        ? { start: el.selectionStart, end: el.selectionEnd }
        : null;
    const tracked = live ?? selectionRef.current;
    const caret = tracked
      ? {
          start: Math.min(tracked.start, value.length),
          end: Math.min(tracked.end, value.length),
        }
      : { start: value.length, end: value.length };
    const abort = new AbortController();
    abortRef.current = abort;
    setDictationError(null);
    setTranscribed(false);
    setDictating(true);
    // The auto-stop timer can overshoot the admitted limit by one tick;
    // the reported duration is clamped so it never exceeds the contract.
    const boundedDraft =
      typeof audioCaptureMaxDurationMs === "number" &&
      draft.durationMs > audioCaptureMaxDurationMs
        ? { ...draft, durationMs: audioCaptureMaxDurationMs }
        : draft;
    dictationTranscriber(boundedDraft, abort.signal)
      .then((result) => {
        if (session !== sessionRef.current) return; // late response discarded
        setDictating(false);
        const merged = mergeTranscriptIntoDraft(
          value,
          caret.start,
          caret.end,
          result.text,
          INTERACTION_INPUT_CHAR_LIMIT,
        );
        caretRef.current = merged.caret;
        onChange(merged.text);
        setTranscribed(true);
        if (merged.truncated) {
          setDictationError(
            "O texto atingiu o limite de caracteres; parte da transcrição foi cortada.",
          );
        }
      })
      .catch((error: unknown) => {
        if (session !== sessionRef.current) return;
        setDictating(false);
        const cancelled =
          error instanceof Error &&
          "code" in error &&
          (error as DeliaDictationError).code === "cancelled";
        if (!cancelled) setDictationError(dictationErrorMessage(error));
      });
  };

  const cancelTranscribing = () => {
    sessionRef.current += 1;
    abortRef.current?.abort();
    abortRef.current = null;
    setDictating(false);
  };

  const sttAdmitted = dictationTranscriber != null;
  // VD-F05: the mic help states the ADMITTED duration (product limit ∧
  // contract limit) — never more than the backend actually accepts.
  const admittedMinutes =
    typeof audioCaptureMaxDurationMs === "number" &&
    audioCaptureMaxDurationMs >= 60_000
      ? Math.floor(audioCaptureMaxDurationMs / 60_000)
      : null;
  const startHelp = sttAdmitted
    ? admittedMinutes != null
      ? `Ditar mensagem — Gravar e transcrever: fale até ${admittedMinutes} minutos e receba o texto ao finalizar.`
      : "Ditar mensagem — Gravar e transcrever: fale e receba o texto ao finalizar."
    : "Gravar áudio neste navegador: a transcrição está indisponível.";

  return (
    <AudioRecorderControl
      enabled={audioCaptureEnabled}
      busy={dictating || (inFlight && !onEnqueue)}
      maxDurationMs={audioCaptureMaxDurationMs}
      maxBytes={audioCaptureMaxBytes}
      canSendAudio={false}
      onDraftReady={handleDraftReady}
      onDiscard={() => setPreviewPending(false)}
      onBlockingChange={setRecorderBlocking}
      helpCopy={{
        startLabel: "Ditar mensagem",
        startHelp,
        unavailableHelp:
          "Ditado indisponível neste navegador ou contexto.",
        finishHelp: sttAdmitted
          ? "Encerrar a gravação e transcrever sua fala para texto."
          : "Encerrar a gravação e ouvir a prévia local.",
      }}
    >
      {({ trigger, panel, status, errorReason, discard }) => {
        discardRef.current = discard;
        return (
          <DeliaComposerBody
            // Modal surface swap: a capture panel OR a real transcribing
            // state replaces the write area inside the same composer
            // surface. Error stays in writing mode with the honest
            // reason in the composer's error slot.
            captureView={
              dictating ? (
                <div
                  className="delpi-ui-audio-recorder delpi-ui-audio-recorder--processing"
                  role="status"
                  aria-live="polite"
                  aria-busy="true"
                >
                  <span
                    className="delpi-ui-audio-recorder__activity"
                    aria-hidden="true"
                  >
                    <i />
                    <i />
                    <i />
                  </span>
                  <span className="delpi-ui-audio-recorder__status-text">
                    Transcrevendo sua fala…
                  </span>
                  <div className="delpi-ui-audio-recorder__actions">
                    <HelpTooltip
                      wrap
                      content="Parar de esperar a transcrição e voltar ao texto. O processamento remoto pode continuar."
                    >
                      <IconButton
                        aria-label="Cancelar transcrição"
                        onClick={cancelTranscribing}
                      >
                        <X size={18} aria-hidden="true" />
                      </IconButton>
                    </HelpTooltip>
                  </div>
                </div>
              ) : panel && status !== "error" ? (
                <div className="delia-dictation">
                  {panel}
                  <p className="delia-dictation__disclosure">
                    {sttAdmitted
                      ? DELIA_DICTATION_STT_DISCLOSURE
                      : DELIA_LOCAL_CAPTURE_DISCLOSURE}
                  </p>
                </div>
              ) : null
            }
            captureStatus={dictating ? "transcribing" : status}
            captureErrorReason={errorReason}
            dictationError={dictationError}
            trigger={trigger}
            inputId={inputId}
            value={value}
            onChange={onChange}
            onSubmit={onSubmit}
            onEnqueue={onEnqueue}
            loading={loading}
            requestMode={requestMode}
            onStop={onStop}
            placeholder={placeholder}
            pendingCaretRef={caretRef}
            transcribed={transcribed}
            onUserEdit={() => setTranscribed(false)}
            onClearDraft={onClearDraft}
            draftRecoveryAction={draftRecoveryAction}
            composerSettingsAction={composerSettingsAction}
          />
        );
      }}
    </AudioRecorderControl>
  );
}

type DeliaComposerBodyProps = {
  captureView: ReactNode;
  captureStatus: string;
  captureErrorReason: string | null;
  dictationError: string | null;
  trigger: ReactNode;
  inputId: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onEnqueue?: () => void;
  loading: boolean;
  requestMode?: DeliaComposerProps["requestMode"];
  onStop?: () => void;
  placeholder: string;
  pendingCaretRef: MutableRefObject<number | null>;
  transcribed: boolean;
  onUserEdit: () => void;
  onClearDraft?: (clearedValue: string) => void;
  draftRecoveryAction?: ReactNode;
  composerSettingsAction?: ReactNode;
};

/** Internal body — component so the focus-restore effect is legal. */
function DeliaComposerBody({
  captureView,
  captureStatus,
  captureErrorReason,
  dictationError,
  trigger,
  inputId,
  value,
  onChange,
  onSubmit,
  onEnqueue,
  loading,
  requestMode,
  onStop,
  placeholder,
  pendingCaretRef,
  transcribed,
  onUserEdit,
  onClearDraft,
  draftRecoveryAction,
  composerSettingsAction,
}: DeliaComposerBodyProps) {
  const captureActive = captureView != null;
  const wasActiveRef: MutableRefObject<boolean> = useRef(captureActive);

  // Focus restoration: leaving capture/transcription back to writing
  // refocuses the (remounted) textarea predictably — after a successful
  // transcript the caret lands right after the inserted text.
  useEffect(() => {
    const wasActive = wasActiveRef.current;
    wasActiveRef.current = captureActive;
    if (wasActive && !captureActive && captureStatus === "idle") {
      const el = document.getElementById(inputId);
      if (el instanceof HTMLTextAreaElement) {
        el.focus();
        const caret = pendingCaretRef.current;
        if (caret != null) {
          el.setSelectionRange(caret, caret);
          pendingCaretRef.current = null;
        }
      }
    }
  }, [captureActive, captureStatus, inputId, pendingCaretRef]);

  const handleUserChange = (next: string) => {
    if (transcribed) onUserEdit();
    onChange(next);
  };

  return (
    <div className="delia-composer-stack">
      <MessageComposer
        className="delia-composer"
        inputId={inputId}
        inputLabel="Pergunte à DÉLIA"
        value={value}
        onChange={handleUserChange}
        onClearDraft={() => {
          onClearDraft?.(value);
          handleUserChange("");
        }}
        onSubmit={onSubmit}
        onEnqueue={onEnqueue}
        loading={loading}
        requestMode={requestMode}
        onStop={onStop}
        placeholder={placeholder}
        characterLimit={INTERACTION_INPUT_CHAR_LIMIT}
        helperText="A DÉLIA pode cometer erros. Confirme informações importantes."
        bodyOverride={captureView ?? undefined}
        secondaryActions={
          captureView ? undefined : (
            <>
              {draftRecoveryAction}
              {trigger}
              {composerSettingsAction}
            </>
          )
        }
        submitDisabled={captureActive}
        error={
          captureStatus === "error"
            ? audioRecorderErrorMessage(captureErrorReason)
            : (dictationError ?? undefined)
        }
      />
      {transcribed && !captureActive ? (
        <p className="delia-composer__transcribed" role="status">
          Texto transcrito. Revise antes de enviar.
        </p>
      ) : null}
    </div>
  );
}


type DeliaComposerIncrementalProps = DeliaComposerProps & {
  transport: IncrementalTransport;
  maxSessionMs: number | null;
  maxSegments: number | null;
};

/**
 * VD-F06 progressive dictation composer — the SAME MessageComposer
 * surface, never a second composer. The textarea stays rendered and
 * editable through the whole capture: speech lands at the real caret/
 * selection via the reconciler, human edits always win over late STT,
 * and Send remains the only submit path (explicit, user-invoked).
 */
function DeliaComposerIncremental({
  inputId,
  value,
  onChange,
  onSubmit,
  onEnqueue,
  loading = false,
  requestMode,
  onStop,
  placeholder = "Pergunte à DÉLIA…",
  transport,
  maxSessionMs,
  maxSegments,
  onClearDraft,
  draftRecoveryAction,
  composerSettingsAction,
  onCaptureActivityChange,
}: DeliaComposerIncrementalProps) {
  const inFlight =
    loading || (requestMode != null && requestMode !== "idle");
  const valueRef = useRef(value);
  valueRef.current = value;
  const dictation = useIncrementalDictation({
    transport,
    inputId,
    getDraft: () => valueRef.current,
    setDraft: (text) => onChange(text),
    maxSessionMs,
    maxSegments,
  });
  const prevValueRef = useRef(value);

  // Mode-switch lock: any active/transitioning capture keeps the
  // dual-mode selector disabled; review/idle releases it.
  useEffect(() => {
    onCaptureActivityChange?.(dictation.active);
  }, [dictation.active, onCaptureActivityChange]);
  useEffect(
    () => () => onCaptureActivityChange?.(false),
    [onCaptureActivityChange],
  );

  // Human edits register with the reconciler FIRST (controller-origin
  // writes are flagged and skipped), then propagate to the host draft.
  const handleUserChange = (next: string) => {
    if (dictation.active && !dictation.isInternalWrite()) {
      dictation.noteUserEdit(prevValueRef.current, next);
    }
    prevValueRef.current = next;
    onChange(next);
  };
  // Keep the tracker honest when the controller writes the draft.
  useEffect(() => {
    prevValueRef.current = value;
  }, [value]);

  // Explicit submit while dictating: stop waiting on unfinished
  // segments first — confirmed + human text stays, pending partials
  // never sneak into a message the user already sent.
  const handleSubmit = () => {
    if (dictation.active) dictation.cancel();
    onSubmit();
  };
  const handleClear = () => {
    dictation.cancel();
    onClearDraft?.(value);
    onChange("");
  };

  const statusText =
    dictation.state === "requesting_permission"
      ? "Solicitando acesso ao microfone…"
      : dictation.state === "listening"
        ? dictation.provisionalText
          ? `Ouvindo… ${dictation.provisionalText}`
          : "Ouvindo…"
        : dictation.state === "paused"
          ? "Ditado em pausa."
          : dictation.state === "finalizing"
            ? "Finalizando a transcrição…"
            : null;

  return (
    <div className="delia-composer-stack">
      <MessageComposer
        className="delia-composer"
        inputId={inputId}
        inputLabel="Pergunte à DÉLIA"
        value={value}
        onChange={handleUserChange}
        onClearDraft={handleClear}
        onSubmit={handleSubmit}
        onEnqueue={onEnqueue}
        loading={loading}
        requestMode={requestMode}
        onStop={onStop}
        placeholder={placeholder}
        characterLimit={INTERACTION_INPUT_CHAR_LIMIT}
        helperText="A DÉLIA pode cometer erros. Confirme informações importantes."
        secondaryActions={
          dictation.active ? (
            <span className="delia-dictation-live__controls">
              {composerSettingsAction}
              {dictation.state === "listening" ? (
                <HelpTooltip
                  wrap
                  content="Pausar a captura de áudio; o texto continua editável."
                >
                  <IconButton
                    aria-label="Pausar ditado"
                    onClick={dictation.pause}
                  >
                    <Pause size={18} aria-hidden="true" />
                  </IconButton>
                </HelpTooltip>
              ) : dictation.state === "paused" ? (
                <HelpTooltip
                  wrap
                  content="Retomar o ditado a partir da posição atual do cursor."
                >
                  <IconButton
                    aria-label="Retomar ditado"
                    onClick={dictation.resume}
                  >
                    <Play size={18} aria-hidden="true" />
                  </IconButton>
                </HelpTooltip>
              ) : null}
              <HelpTooltip
                wrap
                content="Encerrar a captura e concluir a transcrição dos trechos."
              >
                <IconButton
                  aria-label="Finalizar ditado"
                  onClick={dictation.finalize}
                  disabled={dictation.state === "finalizing"}
                >
                  <Square size={18} aria-hidden="true" />
                </IconButton>
              </HelpTooltip>
              <HelpTooltip
                wrap
                content="Descartar a captura: mantém o texto confirmado e suas edições; remove apenas o trecho ainda provisório."
              >
                <IconButton
                  aria-label="Descartar captura"
                  onClick={dictation.cancel}
                >
                  <Trash2 size={18} aria-hidden="true" />
                </IconButton>
              </HelpTooltip>
            </span>
          ) : (
            <>
              {draftRecoveryAction}
              <HelpTooltip
                wrap
                content="Ditar mensagem — Transcrição em tempo real: o texto aparece enquanto você fala e continua editável. O áudio é enviado à transcrição da DÉLIA."
              >
                <IconButton
                  aria-label="Iniciar ditado"
                  onClick={dictation.start}
                  disabled={inFlight && !onEnqueue}
                >
                  <Mic size={18} aria-hidden="true" />
                </IconButton>
              </HelpTooltip>
              {composerSettingsAction}
            </>
          )
        }
        error={dictation.error ?? undefined}
      />
      {dictation.active ? (
        <div
          className="delia-dictation-live"
          role="status"
          aria-live="polite"
        >
          <span
            className="delia-dictation-live__dot"
            data-paused={dictation.state === "paused" ? "true" : "false"}
            aria-hidden="true"
          />
          <span className="delia-dictation-live__status">{statusText}</span>
          <span className="delia-dictation-live__duration">
            {formatAudioDurationMs(dictation.elapsedMs)}
          </span>
          <span
            className="delpi-ui-audio-recorder__wave"
            aria-hidden="true"
            data-live="true"
          >
            {dictation.levels.map((level, index) => (
              <span
                key={index}
                className="delpi-ui-audio-recorder__bar"
                style={{ transform: `scaleY(${Math.max(0.12, level)})` }}
              />
            ))}
          </span>
          <span className="delia-dictation-live__disclosure">
            {DELIA_DICTATION_STT_DISCLOSURE}
          </span>
        </div>
      ) : null}
      {dictation.state === "review" ? (
        <p className="delia-composer__transcribed" role="status">
          Texto transcrito. Revise antes de enviar.
        </p>
      ) : null}
    </div>
  );
}
