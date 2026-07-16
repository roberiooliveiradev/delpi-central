import { useRef } from "react";

import {
  buildAdminPresentationWsUrl,
  usePresentationRealtime,
  type PresentationPresencePeer,
  type PresentationRealtimeEvent,
  type PresentationSlideDraftEvent,
} from "@delpi/tv-dashboard-presentation";

type RealtimeSend = (payload: Record<string, unknown>) => void;

type Options = {
  playlistId: string;
  accessToken?: string;
  presence?: PresentationPresencePeer;
  enabled?: boolean;
  onSync: (event?: PresentationRealtimeEvent) => void;
  onSlideDraft?: (event: PresentationSlideDraftEvent) => void;
  onPresenceUpdate?: (peers: PresentationPresencePeer[]) => void;
};

export function usePlaylistEditorSync({
  playlistId,
  accessToken,
  presence,
  enabled = true,
  onSync,
  onSlideDraft,
  onPresenceUpdate,
}: Options) {
  const wsUrl = accessToken ? buildAdminPresentationWsUrl(playlistId, accessToken) : null;
  const onSyncRef = useRef(onSync);
  onSyncRef.current = onSync;
  const onSlideDraftRef = useRef(onSlideDraft);
  onSlideDraftRef.current = onSlideDraft;
  const sendRef = useRef<RealtimeSend | null>(null);
  const connectedRef = useRef(false);

  usePresentationRealtime({
    enabled: enabled && Boolean(playlistId && wsUrl),
    wsUrl,
    presence,
    sendRef,
    onConnectionChange: (connected) => {
      const wasConnected = connectedRef.current;
      connectedRef.current = connected;
      if (connected && !wasConnected) {
        onSyncRef.current();
      }
    },
    onPresentationUpdated: (event) => {
      onSyncRef.current(event);
    },
    onSlideDraft: (event) => {
      onSlideDraftRef.current?.(event);
    },
    onPresenceUpdate,
  });

  return { sendRealtime: sendRef };
}
