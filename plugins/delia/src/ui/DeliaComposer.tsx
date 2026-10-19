import { useEffect, useRef } from "react";
import type { MutableRefObject, ReactNode } from "react";
import {
  AudioRecorderControl,
  audioRecorderErrorMessage,
  MessageComposer,
} from "@delpi/plugin-ui/index";

import { INTERACTION_INPUT_CHAR_LIMIT } from "../api/interactionClient";

export type DeliaComposerProps = {
  inputId: string;
  value: string;
  onChange: (value: string) => void;
  /** Explicit user intent only — never invoked programmatically. */
  onSubmit: () => void;
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
};

/**
 * DÉLIA composer — thin product wrapper over the plugin-ui
 * `MessageComposer` (single surface, write band + toolbar).
 *
 * Voice Dictation rework (VD-F02): while capture is active, the
 * recorder occupies the SAME composer surface — the textarea and the
 * normal toolbar are not rendered (MessageComposer `bodyOverride`), so
 * no typing or textual send is possible during dictation. The draft is
 * untouched in host state and restored on cancel/discard/error.
 * `canSendAudio` stays false until a real upload contract exists; STT
 * is not implemented — finishing a capture yields a local preview
 * (listen / discard / re-record), never a transcription or auto-send.
 */
export function DeliaComposer({
  inputId,
  value,
  onChange,
  onSubmit,
  loading = false,
  requestMode,
  onStop,
  placeholder = "Pergunte à DÉLIA…",
  audioCaptureEnabled = false,
  audioCaptureMaxDurationMs,
  audioCaptureMaxBytes,
}: DeliaComposerProps) {
  const inFlight =
    loading || (requestMode != null && requestMode !== "idle");

  return (
    <AudioRecorderControl
      enabled={audioCaptureEnabled}
      busy={inFlight}
      maxDurationMs={audioCaptureMaxDurationMs}
      maxBytes={audioCaptureMaxBytes}
      canSendAudio={false}
    >
      {({ trigger, panel, status, errorReason }) => (
        <DeliaComposerBody
          // Modal surface swap: any capture panel (requesting /
          // recording / stopping / preview) replaces the write area
          // inside the same composer surface. Error stays in writing
          // mode with the honest reason in the composer's error slot.
          captureView={panel && status !== "error" ? panel : null}
          captureStatus={status}
          captureErrorReason={errorReason}
          trigger={trigger}
          inputId={inputId}
          value={value}
          onChange={onChange}
          onSubmit={onSubmit}
          loading={loading}
          requestMode={requestMode}
          onStop={onStop}
          placeholder={placeholder}
        />
      )}
    </AudioRecorderControl>
  );
}

type DeliaComposerBodyProps = {
  captureView: ReactNode;
  captureStatus: string;
  captureErrorReason: string | null;
  trigger: ReactNode;
  inputId: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
  requestMode?: DeliaComposerProps["requestMode"];
  onStop?: () => void;
  placeholder: string;
};

/** Internal body — component so the focus-restore effect is legal. */
function DeliaComposerBody({
  captureView,
  captureStatus,
  captureErrorReason,
  trigger,
  inputId,
  value,
  onChange,
  onSubmit,
  loading,
  requestMode,
  onStop,
  placeholder,
}: DeliaComposerBodyProps) {
  const captureActive = captureView != null;
  const wasActiveRef: MutableRefObject<boolean> = useRef(captureActive);

  // Focus restoration: leaving capture back to idle writing refocuses
  // the (remounted) textarea predictably.
  useEffect(() => {
    const wasActive = wasActiveRef.current;
    wasActiveRef.current = captureActive;
    if (wasActive && !captureActive && captureStatus === "idle") {
      const el = document.getElementById(inputId);
      if (el instanceof HTMLTextAreaElement) el.focus();
    }
  }, [captureActive, captureStatus, inputId]);

  return (
    <div className="delia-composer-stack">
      <MessageComposer
        className="delia-composer"
        inputId={inputId}
        inputLabel="Pergunte à DÉLIA"
        value={value}
        onChange={onChange}
        onClearDraft={() => onChange("")}
        onSubmit={onSubmit}
        loading={loading}
        requestMode={requestMode}
        onStop={onStop}
        placeholder={placeholder}
        characterLimit={INTERACTION_INPUT_CHAR_LIMIT}
        helperText="A DÉLIA pode cometer erros. Confirme informações importantes."
        bodyOverride={captureView ?? undefined}
        secondaryActions={captureView ? undefined : (trigger ?? undefined)}
        submitDisabled={captureActive}
        error={
          captureStatus === "error"
            ? audioRecorderErrorMessage(captureErrorReason)
            : undefined
        }
      />
    </div>
  );
}
