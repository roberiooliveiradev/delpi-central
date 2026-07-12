import type { ComunicadoDataResolved } from "@delpi/tv-dashboard-presentation";

import type { Playlist } from "../api/tvDashboardApi";

const PLAYLIST_KEY_PREFIX = "td-editor-playlist:";
const DATA_PREVIEW_KEY_PREFIX = "td-editor-data-preview:";

type DataPreviewCacheEntry = {
  fingerprint: string;
  resolvedByBlockId: Record<string, ComunicadoDataResolved>;
};

function canUseSessionStorage(): boolean {
  return typeof window !== "undefined" && typeof window.sessionStorage !== "undefined";
}

export function readPlaylistShell(playlistId: string): Playlist | null {
  if (!canUseSessionStorage() || !playlistId) return null;
  try {
    const raw = window.sessionStorage.getItem(`${PLAYLIST_KEY_PREFIX}${playlistId}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Playlist;
    if (!parsed || typeof parsed !== "object" || parsed.id !== playlistId) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function writePlaylistShell(playlist: Playlist): void {
  if (!canUseSessionStorage() || !playlist?.id) return;
  try {
    window.sessionStorage.setItem(`${PLAYLIST_KEY_PREFIX}${playlist.id}`, JSON.stringify(playlist));
  } catch {
    // quota / private mode — ignora
  }
}

export function readDataPreviewCache(
  playlistId: string,
  fingerprint: string,
): Record<string, ComunicadoDataResolved> {
  if (!canUseSessionStorage() || !playlistId || !fingerprint) return {};
  try {
    const raw = window.sessionStorage.getItem(`${DATA_PREVIEW_KEY_PREFIX}${playlistId}`);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as DataPreviewCacheEntry;
    if (!parsed || parsed.fingerprint !== fingerprint) return {};
    if (!parsed.resolvedByBlockId || typeof parsed.resolvedByBlockId !== "object") return {};
    return parsed.resolvedByBlockId;
  } catch {
    return {};
  }
}

export function writeDataPreviewCache(
  playlistId: string,
  fingerprint: string,
  resolvedByBlockId: Record<string, ComunicadoDataResolved>,
): void {
  if (!canUseSessionStorage() || !playlistId || !fingerprint) return;
  try {
    const entry: DataPreviewCacheEntry = { fingerprint, resolvedByBlockId };
    window.sessionStorage.setItem(`${DATA_PREVIEW_KEY_PREFIX}${playlistId}`, JSON.stringify(entry));
  } catch {
    // quota / private mode — ignora
  }
}

/** Comparação estrutural — evita setState quando o poll devolve o mesmo payload. */
export function resolvedMapsEqual(
  a: Record<string, ComunicadoDataResolved>,
  b: Record<string, ComunicadoDataResolved>,
): boolean {
  const aKeys = Object.keys(a);
  const bKeys = Object.keys(b);
  if (aKeys.length !== bKeys.length) return false;
  for (const key of aKeys) {
    if (!(key in b)) return false;
    if (JSON.stringify(a[key]) !== JSON.stringify(b[key])) return false;
  }
  return true;
}
