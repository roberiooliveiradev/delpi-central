/**
 * Bounded workspace-context publisher (§6.130 provider-neutral
 * orchestration). The TV Dashboard announces what the user is
 * currently looking at — route/surface hint plus entity references —
 * via a `delpi:workspace-context` CustomEvent on `window`.
 *
 * The Portal owns the registry and hands the latest published
 * context to DÉLIA as an UNTRUSTED hint. This payload never carries
 * authority, permissions, secrets, or provider payloads — only
 * host app identity and entity references the backend may use to
 * ground a capability search (e.g. VISTA get_playlist_context).
 *
 * The event name is frozen by the host contract
 * (`portal/src/utils/workspaceContext.ts`) — keep in sync.
 */

export const DELPI_WORKSPACE_CONTEXT_EVENT = "delpi:workspace-context";

export type WorkspaceEntityRef = {
  entity_type: string;
  entity_id: string;
  source_system: string;
  label?: string;
};

export type TvDashboardWorkspaceContext = {
  host_app_id: "tv-dashboard";
  view_ref: string;
  selected_entity_ref?: WorkspaceEntityRef;
  entity_refs?: WorkspaceEntityRef[];
};

/** Source system recorded on entity refs — VISTA owns playlists/slides. */
export const VISTA_SOURCE_SYSTEM = "vista";

const MAX_REFS = 4;

function publish(context: TvDashboardWorkspaceContext): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent<TvDashboardWorkspaceContext>(
      DELPI_WORKSPACE_CONTEXT_EVENT,
      { detail: context },
    ),
  );
}

/**
 * Announce the playlist currently open — called on route entry and
 * whenever the deck editor selection changes. `selectedSlideId`
 * resolves to a `slide` EntityRef for the owner capability
 * (`vista.get_playlist_context(playlist_id, slide_id)`); the playlist
 * itself is always included as an entity ref so playlist-level
 * questions still ground.
 */
export function publishPlaylistWorkspaceContext(options: {
  playlistId: string;
  viewRef: string;
  selectedSlideId?: string | null;
  playlistLabel?: string;
}): void {
  const playlistRef: WorkspaceEntityRef = {
    entity_type: "playlist",
    entity_id: options.playlistId,
    source_system: VISTA_SOURCE_SYSTEM,
    ...(options.playlistLabel ? { label: options.playlistLabel } : {}),
  };
  const slideRef: WorkspaceEntityRef | undefined = options.selectedSlideId
    ? {
        entity_type: "slide",
        entity_id: options.selectedSlideId,
        source_system: VISTA_SOURCE_SYSTEM,
      }
    : undefined;
  publish({
    host_app_id: "tv-dashboard",
    view_ref: options.viewRef,
    selected_entity_ref: slideRef ?? playlistRef,
    entity_refs: [slideRef, playlistRef]
      .filter(Boolean)
      .slice(0, MAX_REFS) as WorkspaceEntityRef[],
  });
}

/** Announce a playlist-less surface (library, templates, share). */
export function publishSurfaceWorkspaceContext(viewRef: string): void {
  publish({ host_app_id: "tv-dashboard", view_ref: viewRef });
}
