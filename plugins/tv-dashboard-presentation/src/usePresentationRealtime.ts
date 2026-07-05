import { useEffect, useRef } from "react";

export type PresentationRealtimeEvent = {
  type: string;
  reason?: string;
  revision?: string;
  playlistId?: string;
};

type Options = {
  enabled: boolean;
  wsUrl: string | null;
  onPresentationUpdated?: (event: PresentationRealtimeEvent) => void;
  reconnectMs?: number;
  pingMs?: number;
};

export function buildPresentationWsUrl(path: string): string {
  if (typeof window === "undefined") return path;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${path}`;
}

export function buildPublicPresentationWsUrl(token: string): string {
  return buildPresentationWsUrl(
    `/apps/tv-dashboard-api/public/present/${encodeURIComponent(token)}/ws`,
  );
}

export function buildAdminPresentationWsUrl(playlistId: string, accessToken: string): string {
  const base = buildPresentationWsUrl(
    `/apps/tv-dashboard-api/playlists/${encodeURIComponent(playlistId)}/presentation-ws`,
  );
  return `${base}?access_token=${encodeURIComponent(accessToken)}`;
}

export function usePresentationRealtime({
  enabled,
  wsUrl,
  onPresentationUpdated,
  reconnectMs = 5000,
  pingMs = 30000,
}: Options) {
  const handlerRef = useRef(onPresentationUpdated);
  handlerRef.current = onPresentationUpdated;

  useEffect(() => {
    if (!enabled || !wsUrl) return undefined;

    let ws: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let pingTimer: number | null = null;
    let closedByUser = false;

    function scheduleReconnect() {
      if (closedByUser || reconnectTimer != null) return;
      reconnectTimer = window.setTimeout(() => {
        reconnectTimer = null;
        connect();
      }, reconnectMs);
    }

    function connect() {
      if (!wsUrl) return;
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        if (pingTimer != null) window.clearInterval(pingTimer);
        pingTimer = window.setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) ws.send("ping");
        }, pingMs);
      };
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(String(event.data)) as PresentationRealtimeEvent;
          if (payload.type === "presentation_updated") {
            handlerRef.current?.(payload);
          }
        } catch {
          // ignore malformed frames
        }
      };
      ws.onclose = () => {
        if (pingTimer != null) {
          window.clearInterval(pingTimer);
          pingTimer = null;
        }
        if (!closedByUser) scheduleReconnect();
      };
      ws.onerror = () => {
        ws?.close();
      };
    }

    connect();

    return () => {
      closedByUser = true;
      if (reconnectTimer != null) window.clearTimeout(reconnectTimer);
      if (pingTimer != null) window.clearInterval(pingTimer);
      ws?.close();
    };
  }, [enabled, wsUrl, reconnectMs, pingMs]);
}
