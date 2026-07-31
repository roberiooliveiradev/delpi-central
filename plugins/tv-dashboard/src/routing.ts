const PREFIX = "/apps/tv-dashboard";

export type TvDashboardRoute =
  | { view: "list" }
  | { view: "new" }
  | { view: "edit"; id: string }
  | { view: "preview"; id: string }
  | { view: "share"; id: string }
  | { view: "accept-invite"; id: string; token: string }
  | { view: "templates" }
  | { view: "template-edit"; id: string };

export function normalizeTvDashboardPath(pathname?: string) {
  const raw = pathname ?? (typeof window !== "undefined" ? window.location.pathname : PREFIX);
  if (!raw.startsWith(PREFIX)) return PREFIX;
  return raw.replace(/\/+$/, "") || PREFIX;
}

export function parseTvDashboardRoute(path: string, search?: string): TvDashboardRoute {
  const pathOnly = path.split("?")[0] ?? path;
  if (pathOnly === PREFIX) return { view: "list" };

  const templatesRoot = `${PREFIX}/templates`;
  if (pathOnly === templatesRoot) return { view: "templates" };
  const templateEdit = pathOnly.match(/^\/apps\/tv-dashboard\/templates\/([^/]+)$/);
  if (templateEdit?.[1]) return { view: "template-edit", id: templateEdit[1] };

  const playlistsNew = `${PREFIX}/playlists/new`;
  if (pathOnly === playlistsNew) return { view: "new" };

  const acceptMatch = pathOnly.match(
    /^\/apps\/tv-dashboard\/playlists\/([^/]+)\/accept-invite$/,
  );
  if (acceptMatch?.[1]) {
    const query = search
      ?? (path.includes("?") ? path.slice(path.indexOf("?")) : undefined)
      ?? (typeof window !== "undefined" ? window.location.search : "");
    const token = new URLSearchParams(query).get("token")?.trim() ?? "";
    return { view: "accept-invite", id: acceptMatch[1], token };
  }

  const playlistMatch = pathOnly.match(/^\/apps\/tv-dashboard\/playlists\/([^/]+)(?:\/(preview|share))?$/);
  if (playlistMatch?.[1]) {
    const id = playlistMatch[1];
    if (playlistMatch[2] === "preview") return { view: "preview", id };
    if (playlistMatch[2] === "share") return { view: "share", id };
    return { view: "edit", id };
  }

  const legacyMatch = pathOnly.match(/^\/apps\/tv-dashboard\/([^/]+)$/);
  if (
    legacyMatch?.[1] &&
    legacyMatch[1] !== "assets" &&
    legacyMatch[1] !== "playlists" &&
    legacyMatch[1] !== "templates"
  ) {
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

export function playlistAcceptInvitePath(id: string, token: string) {
  return `${PREFIX}/playlists/${id}/accept-invite?token=${encodeURIComponent(token)}`;
}

export function newPlaylistPath() {
  return `${PREFIX}/playlists/new`;
}

export function templatesLibraryPath() {
  return `${PREFIX}/templates`;
}

export function templateEditPath(id: string) {
  return `${PREFIX}/templates/${id}`;
}

export { PREFIX as TV_DASHBOARD_PREFIX };
