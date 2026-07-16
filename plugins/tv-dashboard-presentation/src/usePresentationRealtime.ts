import { useEffect, useRef, type MutableRefObject } from "react";

export type PresentationPresenceRole = "editor" | "viewer";

export type PresentationPresencePeer = {
  clientId: string;
  displayName: string;
  role: PresentationPresenceRole;
};

export type PresentationSlideDraftEvent = {
  type: "slide_draft";
  playlistId?: string;
  slideId: string;
  clientId: string;
  nativeConfig: Record<string, unknown>;
};

export type PresentationSelectionUpdateEvent = {
  type: "selection_update";
  playlistId?: string;
  slideId: string;
  clientId: string;
  displayName: string;
  selectedIds: string[];
  updatedAt?: number;
};

export type PresentationRealtimeEvent = {
  type: string;
  reason?: string;
  revision?: string;
  playlistId?: string;
  slideId?: string;
  clientId?: string;
  nativeConfig?: Record<string, unknown>;
  peers?: PresentationPresencePeer[];
  displayName?: string;
  selectedIds?: string[];
  updatedAt?: number;
};

type RealtimeSend = (payload: Record<string, unknown>) => void;

type Options = {
  enabled: boolean;
  wsUrl: string | null;
  onPresentationUpdated?: (event: PresentationRealtimeEvent) => void;
  onSlideDraft?: (event: PresentationSlideDraftEvent) => void;
  onSelectionUpdate?: (event: PresentationSelectionUpdateEvent) => void;
  onPresenceUpdate?: (peers: PresentationPresencePeer[]) => void;
  onConnectionChange?: (connected: boolean) => void;
  presence?: PresentationPresencePeer;
  sendRef?: React.MutableRefObject<RealtimeSend | null>;
  reconnectMs?: number;
  pingMs?: number;
  updateDebounceMs?: number;
};

export function parsePresentationRealtimeEvent(value: unknown): PresentationRealtimeEvent | null {
  if (!value || typeof value !== "object") return null;
  const payload = value as Record<string, unknown>;
  if (typeof payload.type !== "string") return null;
  if (payload.type === "slide_draft") {
    const slideId = payload.slideId;
    const clientId = payload.clientId;
    const nativeConfig = payload.nativeConfig;
    if (
      typeof slideId !== "string" ||
      typeof clientId !== "string" ||
      !nativeConfig ||
      typeof nativeConfig !== "object" ||
      Array.isArray(nativeConfig)
    ) {
      return null;
    }
    return {
      type: "slide_draft",
      playlistId: typeof payload.playlistId === "string" ? payload.playlistId : undefined,
      slideId,
      clientId,
      nativeConfig: nativeConfig as Record<string, unknown>,
    };
  }
  if (payload.type === "selection_update") {
    const { slideId, clientId, displayName, selectedIds } = payload;
    if (
      typeof slideId !== "string" ||
      typeof clientId !== "string" ||
      typeof displayName !== "string" ||
      !Array.isArray(selectedIds) ||
      !selectedIds.every((item) => typeof item === "string")
    ) {
      return null;
    }
    return {
      type: "selection_update",
      playlistId: typeof payload.playlistId === "string" ? payload.playlistId : undefined,
      slideId,
      clientId,
      displayName,
      selectedIds,
      updatedAt: typeof payload.updatedAt === "number" ? payload.updatedAt : undefined,
    };
  }
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
  onSlideDraft,
  onSelectionUpdate,
  onPresenceUpdate,
  onConnectionChange,
  presence,
  sendRef,
  reconnectMs = 5000,
  pingMs = 30000,
  updateDebounceMs = 200,
}: Options) {
  const handlerRef = useRef(onPresentationUpdated);
  handlerRef.current = onPresentationUpdated;
  const slideDraftHandlerRef = useRef(onSlideDraft);
  slideDraftHandlerRef.current = onSlideDraft;
  const selectionHandlerRef = useRef(onSelectionUpdate);
  selectionHandlerRef.current = onSelectionUpdate;
  const presenceHandlerRef = useRef(onPresenceUpdate);
  presenceHandlerRef.current = onPresenceUpdate;
  const connectionHandlerRef = useRef(onConnectionChange);
  connectionHandlerRef.current = onConnectionChange;
  const sendRefStable = sendRef;
  const updateTimerRef = useRef<number | null>(null);
  const pendingEventRef = useRef<PresentationRealtimeEvent | null>(null);

  useEffect(() => {
    if (!enabled || !wsUrl) {
      connectionHandlerRef.current?.(false);
      if (sendRefStable) sendRefStable.current = null;
      return undefined;
    }

    let ws: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let pingTimer: number | null = null;
    let closedByUser = false;

    function flushPresentationUpdated() {
      updateTimerRef.current = null;
      const payload = pendingEventRef.current;
      pendingEventRef.current = null;
      if (payload) handlerRef.current?.(payload);
    }

    function schedulePresentationUpdated(payload: PresentationRealtimeEvent) {
      pendingEventRef.current = payload;
      if (updateTimerRef.current != null) return;
      updateTimerRef.current = window.setTimeout(flushPresentationUpdated, updateDebounceMs);
    }

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
        connectionHandlerRef.current?.(true);
        if (sendRefStable) {
          sendRefStable.current = (payload) => {
            if (ws?.readyState !== WebSocket.OPEN) return;
            ws.send(JSON.stringify(payload));
          };
        }
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
            schedulePresentationUpdated(payload);
          }
          if (payload.type === "slide_draft") {
            slideDraftHandlerRef.current?.(payload as PresentationSlideDraftEvent);
          }
          if (payload.type === "selection_update") {
            selectionHandlerRef.current?.(payload as PresentationSelectionUpdateEvent);
          }
          if (payload.type === "presence_update") {
            presenceHandlerRef.current?.(payload.peers ?? []);
          }
        } catch {
          // ignore malformed frames
        }
      };
      ws.onclose = () => {
        if (sendRefStable) sendRefStable.current = null;
        connectionHandlerRef.current?.(false);
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
      if (sendRefStable) sendRefStable.current = null;
      connectionHandlerRef.current?.(false);
      if (reconnectTimer != null) window.clearTimeout(reconnectTimer);
      if (pingTimer != null) window.clearInterval(pingTimer);
      if (updateTimerRef.current != null) {
        window.clearTimeout(updateTimerRef.current);
        updateTimerRef.current = null;
      }
      pendingEventRef.current = null;
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
    updateDebounceMs,
    sendRefStable,
    presence?.clientId,
    presence?.displayName,
    presence?.role,
  ]);
}
