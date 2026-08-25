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

export type PresentationPlaybackCursorEvent = {
  type: "playback_cursor";
  playlistId?: string;
  slideId: string;
  clientId: string;
  index?: number | null;
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
  index?: number | null;
};

type RealtimeSend = (payload: Record<string, unknown>) => void;

type Options = {
  enabled: boolean;
  wsUrl: string | null;
  onPresentationUpdated?: (event: PresentationRealtimeEvent) => void;
  onSlideDraft?: (event: PresentationSlideDraftEvent) => void;
  onSelectionUpdate?: (event: PresentationSelectionUpdateEvent) => void;
  onPlaybackCursor?: (event: PresentationPlaybackCursorEvent) => void;
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
  if (payload.type === "playback_cursor") {
    const slideId = payload.slideId;
    const clientId = payload.clientId;
    if (typeof slideId !== "string" || typeof clientId !== "string") return null;
    const index =
      typeof payload.index === "number" && Number.isFinite(payload.index)
        ? payload.index
        : payload.index === null
          ? null
          : undefined;
    return {
      type: "playback_cursor",
      playlistId: typeof payload.playlistId === "string" ? payload.playlistId : undefined,
      slideId,
      clientId,
      index,
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


/** Rota do plugin Painéis TV no portal (presença só vale enquanto estiver aqui). */
export function isTvDashboardPortalPath(pathname: string): boolean {
  const path = (pathname || "").split("?")[0] || "";
  return path === "/apps/tv-dashboard" || path.startsWith("/apps/tv-dashboard/");
}


export function usePresentationRealtime({
  enabled,
  wsUrl,
  onPresentationUpdated,
  onSlideDraft,
  onSelectionUpdate,
  onPlaybackCursor,
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
  const playbackCursorHandlerRef = useRef(onPlaybackCursor);
  playbackCursorHandlerRef.current = onPlaybackCursor;
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
    let pathGuardTimer: number | null = null;
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
          if (payload.type === "playback_cursor") {
            playbackCursorHandlerRef.current?.(payload as PresentationPlaybackCursorEvent);
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

    function sendPresenceLeave() {
      if (!presence || ws?.readyState !== WebSocket.OPEN) return;
      try {
        ws.send(JSON.stringify({ type: "presence_leave", clientId: presence.clientId }));
      } catch {
        // o fechamento da conexão também remove a presença no servidor
      }
    }

    function tearDownPresenceSocket() {
      closedByUser = true;
      if (reconnectTimer != null) {
        window.clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      if (pingTimer != null) {
        window.clearInterval(pingTimer);
        pingTimer = null;
      }
      if (pathGuardTimer != null) {
        window.clearInterval(pathGuardTimer);
        pathGuardTimer = null;
      }
      sendPresenceLeave();
      try {
        ws?.close();
      } catch {
        // ignore
      }
      ws = null;
      if (sendRefStable) sendRefStable.current = null;
      connectionHandlerRef.current?.(false);
      presenceHandlerRef.current?.([]);
    }

    function onPageHide() {
      tearDownPresenceSocket();
    }

    /**
     * SPA: sair do plugin sem fechar a aba não dispara pagehide — o socket de
     * presença do editor ficava vivo. Só aplica com `presence` (editor);
     * kiosk/prévia em `/p/...` devem manter o WS de `presentation_updated`.
     */
    function guardPortalPath() {
      if (!presence) return;
      if (typeof window === "undefined") return;
      if (isTvDashboardPortalPath(window.location.pathname)) return;
      tearDownPresenceSocket();
    }

    connect();

    window.addEventListener("pagehide", onPageHide);
    if (presence) {
      window.addEventListener("popstate", guardPortalPath);
      pathGuardTimer = window.setInterval(guardPortalPath, 1000);
    }

    return () => {
      window.removeEventListener("pagehide", onPageHide);
      window.removeEventListener("popstate", guardPortalPath);
      if (updateTimerRef.current != null) {
        window.clearTimeout(updateTimerRef.current);
        updateTimerRef.current = null;
      }
      pendingEventRef.current = null;
      tearDownPresenceSocket();
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
