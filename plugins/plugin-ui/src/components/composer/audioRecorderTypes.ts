/**
 * Local audio capture draft — transient browser media only.
 * Never serialize into knowledge, memory, prompts or logs.
 */
export type LocalAudioDraft = {
  blob: Blob;
  mimeType: string;
  durationMs: number;
  sizeBytes: number;
};

export type AudioRecorderUiStatus =
  | "unavailable"
  | "idle"
  | "requesting_permission"
  | "recording"
  | "stopping"
  | "preview"
  | "error";

export type AudioRecorderCaptureErrorReason =
  | "permission_denied"
  | "device_not_found"
  | "device_not_readable"
  | "api_unavailable"
  | "mime_unsupported"
  | "recorder_failed"
  | "limit_duration"
  | "limit_bytes"
  | "secure_context_required"
  | "unknown";

/**
 * Product-owned copy overrides for the capture controls' accessible
 * names and contextual help (VD-F04). Defaults describe plain local
 * capture; a dictation product surface passes dictation copy instead.
 */
export type AudioRecorderHelpCopy = {
  /** Accessible name of the idle mic trigger (default "Gravar áudio"). */
  startLabel?: string;
  /** HelpTooltip content on the idle mic trigger. */
  startHelp?: string;
  /** HelpTooltip content on the unavailable (disabled) trigger. */
  unavailableHelp?: string;
  /** HelpTooltip content on the finish-recording control. */
  finishHelp?: string;
};

export type AudioRecorderControlProps = {
  /**
   * Product/consumer admission gate — not backend AuthZ.
   * Without approved maxDurationMs + maxBytes the control stays unavailable.
   */
  enabled: boolean;
  disabled?: boolean;
  /** Blocks starting capture while the host request is in flight. */
  busy?: boolean;
  /** Owner-approved limit; required with maxBytes to leave unavailable. */
  maxDurationMs?: number;
  maxBytes?: number;
  /** Must stay false until a real upload contract exists. */
  canSendAudio?: boolean;
  onDraftReady?: (draft: LocalAudioDraft) => void;
  onDiscard?: () => void;
  onConfirmSend?: (draft: LocalAudioDraft) => void;
  onCaptureError?: (reason: AudioRecorderCaptureErrorReason) => void;
  /** True while recording/stopping/requesting — host should block text submit. */
  onBlockingChange?: (blocking: boolean) => void;
  /** Product copy overrides for control names/help — see type docs. */
  helpCopy?: AudioRecorderHelpCopy;
  className?: string;
};

export function formatAudioDurationMs(ms: number): string {
  const totalSec = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSec / 60);
  const seconds = totalSec % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}
