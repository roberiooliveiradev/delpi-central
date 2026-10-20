/**
 * QA admission for the local audio recorder — mirrors demoMode's gate.
 *
 * Hard gate: the admission is only possible when the bundle runs in Vite
 * dev mode (`import.meta.env.DEV`) or was deliberately built with
 * `VITE_DELIA_AUDIO_QA=1` (a QA/preview environment decision). Even then
 * it activates only via the explicit `?delia-audio-qa=1` query param.
 * Production bundles never enter this path: the URL parameter alone is
 * inert without a bundle-level admission flag.
 *
 * The limits below are QA fixtures, NOT approved production media
 * policy. Production capture requires owner-approved limits and a real
 * product decision (see spec 119 §5/§6).
 */

export const DELIA_AUDIO_QA_QUERY_PARAM = "delia-audio-qa";

/** QA fixture limits — test values only, never production policy. */
export const DELIA_AUDIO_QA_MAX_DURATION_MS = 60_000;
export const DELIA_AUDIO_QA_MAX_BYTES = 256_000;

export type AudioCaptureQaAdmission = {
  maxDurationMs: number;
  maxBytes: number;
};

/** Whether this bundle is even allowed to entertain audio QA. */
export function isAudioQaBundleAllowed(
  env: Pick<ImportMetaEnv, "DEV"> & { VITE_DELIA_AUDIO_QA?: string } =
    import.meta.env,
): boolean {
  return Boolean(env.DEV) || env.VITE_DELIA_AUDIO_QA === "1";
}

/**
 * Resolve the QA admission from the URL query. Returns `null` when the
 * bundle gate is closed or the param is absent/not `1`.
 */
export function resolveAudioQaAdmission(
  search: string,
  env?: Parameters<typeof isAudioQaBundleAllowed>[0],
): AudioCaptureQaAdmission | null {
  if (!isAudioQaBundleAllowed(env)) return null;
  const queryIndex = search.indexOf("?");
  const rawSearch = queryIndex >= 0 ? search.slice(queryIndex + 1) : search;
  const params = new URLSearchParams(rawSearch);
  if (params.get(DELIA_AUDIO_QA_QUERY_PARAM) !== "1") return null;
  return {
    maxDurationMs: DELIA_AUDIO_QA_MAX_DURATION_MS,
    maxBytes: DELIA_AUDIO_QA_MAX_BYTES,
  };
}
