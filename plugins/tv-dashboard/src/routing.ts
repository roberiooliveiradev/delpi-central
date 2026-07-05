const PREFIX = "/apps/tv-dashboard";

export type TvDashboardRoute =
  | { view: "list" }
  | { view: "new" }
  | { view: "edit"; id: string }
  | { view: "preview"; id: string }
  | { view: "share"; id: string };

export function normalizeTvDashboardPath(pathname?: string) {
  const raw = pathname ?? (typeof window !== "undefined" ? window.location.pathname : PREFIX);
  if (!raw.startsWith(PREFIX)) return PREFIX;
  return raw.replace(/\/+$/, "") || PREFIX;
}

export function parseTvDashboardRoute(path: string): TvDashboardRoute {
  if (path === PREFIX) return { view: "list" };

  const playlistsNew = `${PREFIX}/playlists/new`;
  if (path === playlistsNew) return { view: "new" };

  const playlistMatch = path.match(/^\/apps\/tv-dashboard\/playlists\/([^/]+)(?:\/(preview|share))?$/);
  if (playlistMatch?.[1]) {
    const id = playlistMatch[1];
    if (playlistMatch[2] === "preview") return { view: "preview", id };
    if (playlistMatch[2] === "share") return { view: "share", id };
    return { view: "edit", id };
  }

  const legacyMatch = path.match(/^\/apps\/tv-dashboard\/([^/]+)$/);
  if (legacyMatch?.[1] && legacyMatch[1] !== "assets" && legacyMatch[1] !== "playlists") {
    return { view: "edit", id: legacyMatch[1] };
  }

  return { view: "list" };
}

export function playlistPath(id: string) {
  return `${PREFIX}/playlists/${id}`;
}

export function playlistPreviewPath(id: string) {
  return `${PREFIX}/playlists/${id}/preview`;
}

export function playlistSharePath(id: string) {
  return `${PREFIX}/playlists/${id}/share`;
}

export function newPlaylistPath() {
  return `${PREFIX}/playlists/new`;
}

export { PREFIX as TV_DASHBOARD_PREFIX };
