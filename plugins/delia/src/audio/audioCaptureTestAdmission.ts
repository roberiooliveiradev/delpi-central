/**
 * Controlled production-test admission for the local audio recorder.
 *
 * Unlike the QA admission (`audioCaptureQaAdmission.ts`), this path does
 * not depend on build flags or URL parameters: it consumes the
 * Core-resolved `permissions` projection that the Portal host already
 * delivers to the MFE (`AppProps.permissions`, sourced from
 * `MeResponse.permissions` — backend-resolved RBAC, never a frontend
 * claim).
 *
 * The permission `delia.audio-capture.test` is declared in
 * `delpi.manifest.json` and granted to explicitly admitted test users
 * through the canonical Core RBAC pipeline (`/core-api/admin/...`).
 * Revocation is a permission removal — effective on the next host
 * resolution/remount — with no redeploy required. Absent, unresolved or
 * removed permission means fail-closed: no recorder UI.
 *
 * The limits below are bounded test values authorized by the Product
 * Master for `DELIA-UX-AUDIO-RECORDER-CONTROLLED-PRODUCTION-TEST-01`
 * (spec 119 §5/§6) — a test scope decision, not a permanent production
 * media policy. Local capture only: no upload, no transcription, no
 * audio-derived AuthZ.
 */

export const DELIA_AUDIO_TEST_PERMISSION = "delia.audio-capture.test";

export const DELIA_AUDIO_TEST_BANNER =
  "Gravação de áudio em teste. O áudio fica neste navegador e ainda não pode ser enviado à DÉLIA.";

/** Bounded test limits — Product Master authorized test scope. */
export const DELIA_AUDIO_TEST_MAX_DURATION_MS = 60_000;
export const DELIA_AUDIO_TEST_MAX_BYTES = 256_000;

export type AudioCaptureTestAdmission = {
  maxDurationMs: number;
  maxBytes: number;
};

/**
 * Resolve the test admission from the host-delivered permissions
 * projection. Returns `null` (fail-closed) when the projection is
 * absent or the permission is not granted.
 */
export function resolveAudioTestAdmission(
  permissions: readonly string[] | null | undefined,
): AudioCaptureTestAdmission | null {
  if (!permissions?.includes(DELIA_AUDIO_TEST_PERMISSION)) return null;
  return {
    maxDurationMs: DELIA_AUDIO_TEST_MAX_DURATION_MS,
    maxBytes: DELIA_AUDIO_TEST_MAX_BYTES,
  };
}
