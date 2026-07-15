import { useMemo, useRef } from "react";

import { configureHttpClient } from "./api/httpClient";
import { ConfirmDialogProvider } from "./context/ConfirmDialogProvider";
import { NoticeDialogProvider } from "./context/NoticeDialogProvider";
import { useTvDashboardPath } from "./hooks/useTvDashboardPath";
import { NewPlaylistPage } from "./pages/NewPlaylistPage";
import { PlaylistEditorPage } from "./pages/PlaylistEditorPage";
import { PlaylistPreviewPage } from "./pages/PlaylistPreviewPage";
import { AcceptPlaylistInvitePage, PlaylistSharePage } from "./pages/PlaylistSharePage";
import { PlaylistsPage } from "./pages/PlaylistsPage";
import {
  newPlaylistPath,
  normalizeTvDashboardPath,
  parseTvDashboardRoute,
  playlistPath,
  playlistPreviewPath,
  playlistSharePath,
} from "./routing";
import {
  isDeckEditorSurfaceActive,
  shouldKeepEditorUnderPreview,
} from "./utils/editorSurface";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export { isDeckEditorSurfaceActive, shouldKeepEditorUnderPreview } from "./utils/editorSurface";

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useTvDashboardPath(pathnameFromHost);
  const path = normalizeTvDashboardPath(pathname);
  const route = useMemo(
    () =>
      parseTvDashboardRoute(
        path,
        typeof window !== "undefined" ? window.location.search : undefined,
      ),
    [path],
  );

  const editorSessionPlaylistIdRef = useRef<string | null>(null);
  if (route.view === "edit") {
    editorSessionPlaylistIdRef.current = route.id;
  } else if (route.view !== "preview") {
    editorSessionPlaylistIdRef.current = null;
  }

  const isFullscreenView = route.view === "preview";
  const isDeckEditor = route.view === "edit";
  const playlistId =
    route.view === "edit" || route.view === "preview" || route.view === "share"
      ? route.id
      : undefined;
  const keepEditor = shouldKeepEditorUnderPreview(
    route.view,
    playlistId,
    editorSessionPlaylistIdRef.current,
  );
  const deckChrome = isDeckEditor || (isFullscreenView && keepEditor);

  function navigate(next: string) {
    if (typeof window === "undefined") return;
    window.history.pushState({}, "", next);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }

  function renderBody() {
    switch (route.view) {
      case "list":
        return (
          <PlaylistsPage
            onOpen={(id) => navigate(playlistPath(id))}
            onCreate={() => navigate(newPlaylistPath())}
          />
        );
      case "new":
        return (
          <NewPlaylistPage
            onBack={() => navigate("/apps/tv-dashboard")}
            onCreated={(id) => navigate(playlistPath(id))}
          />
        );
      case "share":
        return (
          <PlaylistSharePage
            playlistId={route.id}
            onBack={() => navigate(playlistPath(route.id))}
          />
        );
      case "accept-invite":
        return (
          <AcceptPlaylistInvitePage
            playlistId={route.id}
            token={route.token}
            onDone={(id) => navigate(playlistPath(id))}
          />
        );
      case "edit":
      case "preview":
        return (
          <>
            {keepEditor && playlistId ? (
              <div
                className={
                  route.view === "preview"
                    ? "td-deck-editor-host td-deck-editor-host--under-preview"
                    : "td-deck-editor-host"
                }
                aria-hidden={route.view === "preview"}
              >
                <PlaylistEditorPage
                  playlistId={playlistId}
                  editorActive={isDeckEditorSurfaceActive(route.view)}
                  onBack={() => navigate("/apps/tv-dashboard")}
                  onPreview={() => navigate(playlistPreviewPath(playlistId))}
                  onShare={() => navigate(playlistSharePath(playlistId))}
                />
              </div>
            ) : null}
            {route.view === "preview" ? (
              <PlaylistPreviewPage
                playlistId={route.id}
                onBack={() => navigate(playlistPath(route.id))}
              />
            ) : null}
          </>
        );
      default:
        return null;
    }
  }

  return (
    <NoticeDialogProvider>
      <ConfirmDialogProvider>
        <div
          className={[
            "dashboard-tv-dashboard",
            "dashboard-page",
            isFullscreenView ? "td-app-shell--preview" : null,
            deckChrome ? "dashboard-page--deck-edit" : null,
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <div className={`td-app-shell${deckChrome ? " td-app-shell--deck" : ""}`}>
            {!isFullscreenView && !isDeckEditor ? (
              <header className="td-hero">
                <p className="td-eyebrow">Operações · Displays</p>
                <h1 className="td-title">Painéis TV</h1>
                <p className="td-subtitle">
                  Crie programações rotativas para TVs da empresa e compartilhe um link público sem login.
                </p>
              </header>
            ) : null}
            <div className={deckChrome ? "td-app-shell__body td-app-shell__body--deck" : "td-app-shell__body"}>
              {renderBody()}
            </div>
          </div>
        </div>
      </ConfirmDialogProvider>
    </NoticeDialogProvider>
  );
}
