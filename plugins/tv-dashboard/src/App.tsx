import { useMemo } from "react";

import { configureHttpClient } from "./api/httpClient";
import { useTvDashboardDeckLayout } from "./hooks/useTvDashboardDeckLayout";
import { useTvDashboardPath } from "./hooks/useTvDashboardPath";
import { NewPlaylistPage } from "./pages/NewPlaylistPage";
import { PlaylistEditorPage } from "./pages/PlaylistEditorPage";
import { PlaylistPreviewPage } from "./pages/PlaylistPreviewPage";
import { PlaylistSharePage } from "./pages/PlaylistSharePage";
import { PlaylistsPage } from "./pages/PlaylistsPage";
import {
  newPlaylistPath,
  normalizeTvDashboardPath,
  parseTvDashboardRoute,
  playlistPath,
  playlistPreviewPath,
  playlistSharePath,
} from "./routing";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useTvDashboardPath(pathnameFromHost);
  const path = normalizeTvDashboardPath(pathname);
  const route = useMemo(() => parseTvDashboardRoute(path), [path]);

  const isFullscreenView = route.view === "preview";
  const isDeckEditor = route.view === "edit";

  useTvDashboardDeckLayout(isDeckEditor);

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
      case "preview":
        return (
          <PlaylistPreviewPage
            playlistId={route.id}
            onBack={() => navigate(playlistPath(route.id))}
          />
        );
      case "share":
        return (
          <PlaylistSharePage
            playlistId={route.id}
            onBack={() => navigate(playlistPath(route.id))}
          />
        );
      case "edit":
        return (
          <PlaylistEditorPage
            playlistId={route.id}
            onBack={() => navigate("/apps/tv-dashboard")}
            onPreview={() => navigate(playlistPreviewPath(route.id))}
            onShare={() => navigate(playlistSharePath(route.id))}
          />
        );
      default:
        return null;
    }
  }

  return (
    <div
      className={[
        "dashboard-tv-dashboard",
        "dashboard-page",
        isFullscreenView ? "td-app-shell--preview" : null,
        isDeckEditor ? "dashboard-page--deck-edit" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className={`td-app-shell${isDeckEditor ? " td-app-shell--deck" : ""}`}>
        {!isFullscreenView && !isDeckEditor ? (
          <header className="td-hero">
            <p className="td-eyebrow">Operações · Displays</p>
            <h1 className="td-title">Painéis TV</h1>
            <p className="td-subtitle">
              Crie programações rotativas para TVs da empresa e compartilhe um link público sem login.
            </p>
          </header>
        ) : null}
        <div className={isDeckEditor ? "td-app-shell__body td-app-shell__body--deck" : "td-app-shell__body"}>
          {renderBody()}
        </div>
      </div>
    </div>
  );
}
