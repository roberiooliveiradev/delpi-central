import { useEffect, useRef } from "react";

export type PresentationPresenceRole = "editor" | "viewer";

export type PresentationPresencePeer = {
  clientId: string;
  displayName: string;
  role: PresentationPresenceRole;
};

export type PresentationRealtimeEvent = {
  type: string;
  reason?: string;
  revision?: string;
  playlistId?: string;
  peers?: PresentationPresencePeer[];
};

type Options = {
  enabled: boolean;
  wsUrl: string | null;
  onPresentationUpdated?: (event: PresentationRealtimeEvent) => void;
  onPresenceUpdate?: (peers: PresentationPresencePeer[]) => void;
  presence?: PresentationPresencePeer;
  reconnectMs?: number;
  pingMs?: number;
};

export function parsePresentationRealtimeEvent(value: unknown): PresentationRealtimeEvent | null {
  if (!value || typeof value !== "object") return null;
  const payload = value as Record<string, unknown>;
  if (typeof payload.type !== "string") return null;
  if (payload.type !== "presence_update") return payload as PresentationRealtimeEvent;
  if (!Array.isArray(payload.peers)) return null;

  const peers = payload.peers.filter(
    (peer): peer is PresentationPresencePeer =>
      Boolean(peer) &&
      typeof peer === "object" &&
      typeof (peer as PresentationPresencePeer).clientId === "string" &&
      typeof (peer as PresentationPresencePeer).displayName === "string" &&
      ["editor", "viewer"].includes((peer as PresentationPresencePeer).role),
  );
  return { ...(payload as PresentationRealtimeEvent), peers };
}

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
  onPresenceUpdate,
  presence,
  reconnectMs = 5000,
  pingMs = 30000,
}: Options) {
  const handlerRef = useRef(onPresentationUpdated);
  handlerRef.current = onPresentationUpdated;
  const presenceHandlerRef = useRef(onPresenceUpdate);
  presenceHandlerRef.current = onPresenceUpdate;

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
        if (presence) {
          ws?.send(JSON.stringify({ type: "presence_join", ...presence }));
        }
        if (pingTimer != null) window.clearInterval(pingTimer);
        pingTimer = window.setInterval(() => {
          if (ws?.readyState !== WebSocket.OPEN) return;
          ws.send(
            presence
              ? JSON.stringify({ type: "presence_ping", clientId: presence.clientId })
              : "ping",
          );
        }, pingMs);
      };
      ws.onmessage = (event) => {
        try {
          const payload = parsePresentationRealtimeEvent(JSON.parse(String(event.data)));
          if (!payload) return;
          if (payload.type === "presentation_updated") {
            handlerRef.current?.(payload);
          }
          if (payload.type === "presence_update") {
            presenceHandlerRef.current?.(payload.peers ?? []);
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
        presenceHandlerRef.current?.([]);
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
      if (presence && ws?.readyState === WebSocket.OPEN) {
        try {
          ws.send(JSON.stringify({ type: "presence_leave", clientId: presence.clientId }));
        } catch {
          // o fechamento da conexão também remove a presença no servidor
        }
      }
      ws?.close();
    };
  }, [
    enabled,
    wsUrl,
    reconnectMs,
    pingMs,
    presence?.clientId,
    presence?.displayName,
    presence?.role,
  ]);
}
