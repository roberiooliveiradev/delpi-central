import { useRef } from "react";

import {
  buildPlaylistLibraryWsUrl,
  usePresentationRealtime,
  type PresentationRealtimeEvent,
} from "@delpi/tv-dashboard-presentation";

type Options = {
  accessToken?: string;
  enabled?: boolean;
  onLibraryUpdated: (event?: PresentationRealtimeEvent) => void;
};

/** Soft-live sync for PlaylistsPage (user-library WebSocket). */
export function usePlaylistLibrarySync({
  accessToken,
  enabled = true,
  onLibraryUpdated,
}: Options) {
  const wsUrl = accessToken ? buildPlaylistLibraryWsUrl(accessToken) : null;
  const onUpdatedRef = useRef(onLibraryUpdated);
  onUpdatedRef.current = onLibraryUpdated;
  const connectedRef = useRef(false);

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
