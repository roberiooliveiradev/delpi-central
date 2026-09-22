import { useCallback, useEffect, useRef, useState } from "react";

import {
  buildPlaylistLibraryWsUrl,
  usePresentationRealtime,
  type PresentationRealtimeEvent,
} from "@delpi/tv-dashboard-presentation";

import { getAccessToken } from "../api/httpClient";

type Options = {
  enabled?: boolean;
  onLibraryUpdated: (event?: PresentationRealtimeEvent) => void;
};

/**
 * Soft-live sync for PlaylistsPage (user-library WebSocket).
 * Token is polled — host Keycloak may resolve after first paint.
 */
export function usePlaylistLibrarySync({
  enabled = true,
  onLibraryUpdated,
}: Options) {
  const [accessToken, setAccessToken] = useState<string | undefined>(() => getAccessToken());
  const onUpdatedRef = useRef(onLibraryUpdated);
  onUpdatedRef.current = onLibraryUpdated;
  const connectedRef = useRef(false);

  useEffect(() => {
    function syncToken() {
      const next = getAccessToken();
      setAccessToken((prev) => (prev === next ? prev : next));
    }
    syncToken();
    const timer = window.setInterval(syncToken, 2000);
    window.addEventListener("focus", syncToken);
    document.addEventListener("visibilitychange", syncToken);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", syncToken);
      document.removeEventListener("visibilitychange", syncToken);
    };
  }, []);

  const wsUrl = accessToken ? buildPlaylistLibraryWsUrl(accessToken) : null;

  usePresentationRealtime({
    enabled: enabled && Boolean(wsUrl),
    wsUrl,
    onConnectionChange: (connected) => {
      const wasConnected = connectedRef.current;
      connectedRef.current = connected;
      if (connected && !wasConnected) {
        onUpdatedRef.current();
      }
    },
    onPresentationUpdated: (event) => {
      onUpdatedRef.current(event);
    },
  });
}

/** Soft-reload when the tab becomes visible again (WS may have been down). */
export function useLibrarySoftRefreshOnFocus(onRefresh: () => void) {
  const onRefreshRef = useRef(onRefresh);
  onRefreshRef.current = onRefresh;

  const refresh = useCallback(() => {
    onRefreshRef.current();
  }, []);

  useEffect(() => {
    function onVisible() {
      if (document.visibilityState === "visible") {
        refresh();
      }
    }
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", onVisible);
    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", onVisible);
    };
  }, [refresh]);
}
