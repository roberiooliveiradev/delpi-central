/** Playback mode for TV presentation — English contract; UI labels stay PT-BR. */
export type PlaybackMode = "presentation" | "meeting";

export const DEFAULT_PLAYBACK_MODE: PlaybackMode = "presentation";

export function parsePlaybackMode(value: unknown): PlaybackMode | null {
  const raw = typeof value === "string" ? value.trim().toLowerCase() : "";
  if (raw === "presentation" || raw === "meeting") return raw;
  return null;
}

/**
 * Effective mode: query → session override → playlist default → presentation.
 * Callers pass already-normalized pieces; first non-null wins in that order.
 */
export function resolvePlaybackMode(input: {
  queryMode?: string | null;
  sessionMode?: string | null;
  playlistMode?: string | null;
}): PlaybackMode {
  return (
    parsePlaybackMode(input.queryMode) ??
    parsePlaybackMode(input.sessionMode) ??
    parsePlaybackMode(input.playlistMode) ??
    DEFAULT_PLAYBACK_MODE
  );
}

export function isAutoAdvanceMode(mode: PlaybackMode): boolean {
  return mode === "presentation";
}

export function playbackModeLabel(mode: PlaybackMode): string {
  return mode === "meeting" ? "Reunião" : "Apresentação";
}
