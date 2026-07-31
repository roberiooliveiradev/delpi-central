/** UUID canônico (playlist real). Sentinels do editor de template não passam. */
const PLAYLIST_UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/**
 * `playlistId` só vai no preview-block quando é UUID de programação.
 * Sentinels (`template-library`, etc.) omitem o campo — a API resolve sem dataDefaults.
 */
export function resolvePreviewPlaylistId(
  playlistId: string | null | undefined,
): string | undefined {
  const trimmed = typeof playlistId === "string" ? playlistId.trim() : "";
  if (!trimmed) return undefined;
  return PLAYLIST_UUID_RE.test(trimmed) ? trimmed : undefined;
}
