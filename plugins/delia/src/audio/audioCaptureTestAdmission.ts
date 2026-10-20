/**
 * Local audio recorder — bounded test availability.
 *
 * Product Master decision `DELIA-UX-AUDIO-RECORDER-REMOVE-EXTRA-PERMISSION-AND-PRODUCTION-FIX-01`:
 * there is NO dedicated audio permission. The recorder is available to
 * every user legitimately admitted to DÉLIA — `delia.access`, enforced
 * upstream by the Portal/Core before this MFE ever mounts. No extra
 * RBAC permission, query parameter, build flag, or client-side claim
 * gates local capture.
 *
 * Browser support and secure context stay fail-closed inside
 * `AudioRecorderControl`/`useLocalAudioRecorder`
 * (`isLocalAudioCaptureSupported`), and capture still requires an
 * explicit user gesture plus the browser's own mic consent.
 *
 * The limits below are the product-approved capture bounds (VD-F05:
 * 300 s per segment, bytes aligned to the dictation contract). The
 * effective admission is `min(product limits, contract limits)` —
 * see `resolveAudioCaptureLimits`. This module owns frontend admission
 * only; upload/transcription limits remain governed by the backend.
 */

/**
 * Honest purpose/consent copy shown contextually inside the capture
 * surface while dictation.transcription.v1 is available (VD-F03/VD-F04):
 * the audio DOES leave the device — only to the dictation contract,
 * never to multimodal analysis — and returns as editable draft text.
 * Rendered before the audio is transmitted, never as a global header
 * banner (the permanent yellow strip was removed by the Product Master).
 */
export const DELIA_DICTATION_STT_DISCLOSURE =
  "Sua fala será enviada apenas para transcrição em texto. Revise o resultado antes de enviar.";

/**
 * Contextual copy shown while capturing when the dictation contract is
 * NOT available: the capture stays an honest local preview and the
 * audio never leaves the browser.
 */
export const DELIA_LOCAL_CAPTURE_DISCLOSURE =
  "Gravação local: o áudio fica neste navegador e não é enviado à DÉLIA.";

/**
 * Product-approved capture limits (VD-F05, spec 119 §VD-F05):
 * up to 300 seconds per dictation segment. Bytes follow the governed
 * dictation contract bound (8 MiB) — measured evidence: a real 300 s
 * Chrome `audio/webm;codecs=opus` capture exceeds 4 MiB (~4.8 MB at
 * ~128 kbps), so 8 MiB covers 300 s with headroom while staying
 * bounded; oversized captures still stop fail-closed with a typed
 * reason.
 */
export const DELIA_AUDIO_PRODUCT_MAX_DURATION_MS = 300_000;
export const DELIA_AUDIO_PRODUCT_MAX_BYTES = 8_388_608;

export type AudioCaptureLimits = {
  maxDurationMs: number;
  maxBytes: number;
};

/**
 * Limits applied to every legitimately admitted DÉLIA session. Access
 * to the app itself remains owned by Core RBAC (`delia.access`) —
 * this module never decides who may enter the app.
 */
export const DELIA_AUDIO_PRODUCT_LIMITS: AudioCaptureLimits = {
  maxDurationMs: DELIA_AUDIO_PRODUCT_MAX_DURATION_MS,
  maxBytes: DELIA_AUDIO_PRODUCT_MAX_BYTES,
};

/** Structural subset of `DeliaDictationStatus` limits reported by the
 *  dictation contract status endpoint (dictation.transcription.v1). */
export type DictationContractLimits = {
  maxDurationMs: number | null;
  maxAudioBytes: number | null;
};

/**
 * Effective capture admission = min(product decision, contract limits)
 * when the backend publishes numeric limits; product limits otherwise
 * (honest local preview still needs a bound). The composer never
 * announces a duration the admitted contract does not accept.
 */
export function resolveAudioCaptureLimits(
  contractStatus: DictationContractLimits | null,
): AudioCaptureLimits {
  return {
    maxDurationMs: Math.min(
      DELIA_AUDIO_PRODUCT_MAX_DURATION_MS,
      contractStatus?.maxDurationMs ?? DELIA_AUDIO_PRODUCT_MAX_DURATION_MS,
    ),
    maxBytes: Math.min(
      DELIA_AUDIO_PRODUCT_MAX_BYTES,
      contractStatus?.maxAudioBytes ?? DELIA_AUDIO_PRODUCT_MAX_BYTES,
    ),
  };
}
