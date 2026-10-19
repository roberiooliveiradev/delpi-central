import { useState } from "react";
import {
  AudioRecorderControl,
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
   * Remains off in production until media limits are approved.
   * Does not enable upload, transcription, or remote send.
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
 * Optional local audio capture composes via `secondaryActions` and a
 * panel above the composer. Capture stays gated; `canSendAudio` is always
 * false until a real upload contract exists.
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
  const [audioBlocking, setAudioBlocking] = useState(false);
  const inFlight =
    loading || (requestMode != null && requestMode !== "idle");

  return (
    <AudioRecorderControl
      enabled={audioCaptureEnabled}
      busy={inFlight}
      maxDurationMs={audioCaptureMaxDurationMs}
      maxBytes={audioCaptureMaxBytes}
      canSendAudio={false}
      onBlockingChange={setAudioBlocking}
    >
      {({ trigger, panel, blocking }) => (
        <div className="delia-composer-stack">
          {panel}
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
            secondaryActions={trigger ?? undefined}
            submitDisabled={blocking || audioBlocking}
          />
        </div>
      )}
    </AudioRecorderControl>
  );
}
