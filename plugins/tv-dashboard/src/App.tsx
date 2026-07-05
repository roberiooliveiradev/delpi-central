import { useMemo } from "react";

import { configureHttpClient } from "./api/httpClient";
import { useTvDashboardPath } from "./hooks/useTvDashboardPath";
import { PlaylistEditorPage } from "./pages/PlaylistEditorPage";
import { PlaylistsPage } from "./pages/PlaylistsPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

function normalizePath(pathname?: string) {
  const base = "/apps/tv-dashboard";
  const raw = pathname ?? (typeof window !== "undefined" ? window.location.pathname : base);
  if (!raw.startsWith(base)) return base;
  return raw.replace(/\/+$/, "") || base;
}

function parseRoute(path: string): { view: "list" } | { view: "edit"; id: string } {
  const prefix = "/apps/tv-dashboard";
  if (path === prefix) return { view: "list" };
  const match = path.match(/^\/apps\/tv-dashboard\/([^/]+)$/);
  if (match?.[1] && match[1] !== "assets") {
    return { view: "edit", id: match[1] };
  }
  return { view: "list" };
}

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useTvDashboardPath(pathnameFromHost);
  const path = normalizePath(pathname);
  const route = useMemo(() => parseRoute(path), [path]);

  function navigate(next: string) {
    if (typeof window === "undefined") return;
    window.history.pushState({}, "", next);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }

  return (
    <div className="dashboard-tv-dashboard dashboard-page">
      <div className="td-app-shell">
        <header className="td-hero">
          <p className="td-eyebrow">Operações · Displays</p>
          <h1 className="td-title">Painéis TV</h1>
          <p className="td-subtitle">
            Crie programações rotativas para TVs da empresa e compartilhe um link público sem login.
          </p>
        </header>

        {route.view === "list" ? (
          <PlaylistsPage onOpen={(id) => navigate(`/apps/tv-dashboard/${id}`)} />
        ) : (
          <PlaylistEditorPage
            playlistId={route.id}
            onBack={() => navigate("/apps/tv-dashboard")}
          />
        )}
      </div>
    </div>
  );
}
