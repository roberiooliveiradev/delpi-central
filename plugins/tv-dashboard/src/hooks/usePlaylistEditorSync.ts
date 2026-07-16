import { useCallback, useEffect, useRef } from "react";

import {
  buildAdminPresentationWsUrl,
  usePresentationRealtime,
  type PresentationPresencePeer,
  type PresentationRealtimeEvent,
} from "@delpi/tv-dashboard-presentation";

type Options = {
  playlistId: string;
  accessToken?: string;
  presence?: PresentationPresencePeer;
  enabled?: boolean;
  onSync: (event?: PresentationRealtimeEvent) => void;
  onPresenceUpdate?: (peers: PresentationPresencePeer[]) => void;
  fetchContentRevision: (playlistId: string) => Promise<string | null | undefined>;
  pollIntervalConnectedMs?: number;
  pollIntervalDisconnectedMs?: number;
};

export function usePlaylistEditorSync({
  playlistId,
  accessToken,
  presence,
  enabled = true,
  onSync,
  onPresenceUpdate,
  fetchContentRevision,
  pollIntervalConnectedMs = 12_000,
  pollIntervalDisconnectedMs = 4_000,
}: Options) {
  const wsUrl = accessToken ? buildAdminPresentationWsUrl(playlistId, accessToken) : null;
  const wsConnectedRef = useRef(false);
  const lastRevisionRef = useRef<string | null>(null);
  const onSyncRef = useRef(onSync);
  onSyncRef.current = onSync;

  const applyRevision = useCallback((revision: string | null | undefined, event?: PresentationRealtimeEvent) => {
    if (!revision) {
      onSyncRef.current(event);
      return;
    }
    if (lastRevisionRef.current != null && revision === lastRevisionRef.current) {
      return;
    }
    lastRevisionRef.current = revision;
    onSyncRef.current(event);
  }, []);

  usePresentationRealtime({
    enabled: enabled && Boolean(playlistId && wsUrl),
    wsUrl,
    presence,
    onConnectionChange: (connected) => {
      wsConnectedRef.current = connected;
    },
    onPresentationUpdated: (event) => {
      applyRevision(event.revision, event);
    },
    onPresenceUpdate,
  });

  useEffect(() => {
    if (!enabled || !playlistId) return undefined;

    let cancelled = false;
    let timer: number | null = null;

    async function poll() {
      if (cancelled || document.visibilityState === "hidden") return;
      try {
        const revision = await fetchContentRevision(playlistId);
        if (cancelled || revision == null) return;
        if (lastRevisionRef.current == null) {
          lastRevisionRef.current = revision;
          return;
        }
        applyRevision(revision);
      } catch {
        // ignora falha transitória de rede
      }
    }

    function scheduleNextPoll() {
      if (timer != null) window.clearTimeout(timer);
      const delay = wsConnectedRef.current ? pollIntervalConnectedMs : pollIntervalDisconnectedMs;
      timer = window.setTimeout(() => {
        void poll().finally(scheduleNextPoll);
      }, delay);
    }

    void poll().finally(scheduleNextPoll);

    return () => {
      cancelled = true;
      if (timer != null) window.clearTimeout(timer);
    };
  }, [
    applyRevision,
    enabled,
    fetchContentRevision,
    playlistId,
    pollIntervalConnectedMs,
    pollIntervalDisconnectedMs,
  ]);
}
