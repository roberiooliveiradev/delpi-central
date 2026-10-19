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
 * The limits below are bounded test values authorized by the Product
 * Master (spec 119 §5/§6) — a test scope decision, not a permanent
 * production media policy. Local capture only: no upload, no
 * transcription, no audio-derived AuthZ.
 */

export const DELIA_AUDIO_TEST_BANNER =
  "Gravação de áudio em teste. O áudio fica neste navegador e ainda não pode ser enviado à DÉLIA.";

/**
 * Honest purpose/consent copy shown when dictation.transcription.v1 is
 * available (VD-F03): the audio DOES leave the device — only to the
 * dictation contract, never to multimodal analysis — and returns as
 * editable draft text. Shown in place of the local-only test banner.
 */
export const DELIA_DICTATION_STT_BANNER =
  "Ditado por voz: sua fala é enviada apenas para transcrição em texto. Revise o texto antes de enviar.";

/** Bounded test limits — Product Master authorized test scope. */
export const DELIA_AUDIO_TEST_MAX_DURATION_MS = 60_000;
export const DELIA_AUDIO_TEST_MAX_BYTES = 256_000;

export type AudioCaptureLimits = {
  maxDurationMs: number;
  maxBytes: number;
};

/**
 * Limits applied to every legitimately admitted DÉLIA session. Access
 * to the app itself remains owned by Core RBAC (`delia.access`) —
 * this module never decides who may enter the app.
 */
export const DELIA_AUDIO_TEST_LIMITS: AudioCaptureLimits = {
  maxDurationMs: DELIA_AUDIO_TEST_MAX_DURATION_MS,
  maxBytes: DELIA_AUDIO_TEST_MAX_BYTES,
};
