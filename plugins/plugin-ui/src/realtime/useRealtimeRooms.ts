import { useEffect, useRef, useState } from "react";

import {
  RealtimeSocketClient,
  createEventDispatcher,
  type RealtimeConnectionStatus,
  type RealtimeSocketOptions,
} from "./realtimeSocket";

export type UseRealtimeRoomsOptions = {
  enabled: boolean;
  client?: RealtimeSocketClient | null;
  config?: RealtimeSocketOptions;
  rooms: string[];
  onEvent: (events: unknown[]) => void;
  debounceMs?: number;
  onResync?: () => void;
  /** Default: envia o nome da sala como payload (compatível com Engineering). */
  encodeSubscribe?: (room: string) => string;
  encodeUnsubscribe?: (room: string) => string;
};

export function useRealtimeRooms({
  enabled,
  client,
  config,
  rooms,
  onEvent,
  debounceMs,
  onResync,
  encodeSubscribe,
  encodeUnsubscribe,
}: UseRealtimeRoomsOptions): { status: RealtimeConnectionStatus } {
  const [status, setStatus] = useState<RealtimeConnectionStatus>("idle");
  const onEventRef = useRef(onEvent);
  const onResyncRef = useRef(onResync);
  const encodeSubscribeRef = useRef(encodeSubscribe);
  const encodeUnsubscribeRef = useRef(encodeUnsubscribe);
  onEventRef.current = onEvent;
  onResyncRef.current = onResync;
  encodeSubscribeRef.current = encodeSubscribe;
  encodeUnsubscribeRef.current = encodeUnsubscribe;
  const roomsKey = rooms.join("\n");

  useEffect(() => {
    if (!enabled) {
      setStatus("idle");
      return;
    }
    const active =
      client ??
      (config
        ? new RealtimeSocketClient({
            ...config,
            onResync: () => {
              config.onResync?.();
              onResyncRef.current?.();
            },
          })
        : null);
    if (!active) return;
    const stopStatus = active.onStatusChange(setStatus);
    setStatus(active.getStatus());
    const ownsClient = !client;
    if (active.getStatus() === "idle" || active.getStatus() === "closed") {
      active.start();
    }
    const dispatch = createEventDispatcher({
      debounceMs,
      onFlush: (events) => onEventRef.current(events),
    });
    const stopMessages = active.addMessageListener((raw) => {
      try {
        const parsed = JSON.parse(raw) as { eventId?: unknown };
        if (parsed && typeof parsed.eventId === "string" && parsed.eventId) {
          dispatch(parsed);
        }
      } catch {
        // mensagem que não é JSON de evento
      }
    });
    const wanted = roomsKey ? roomsKey.split("\n") : [];
    const toSub = (room: string) =>
      encodeSubscribeRef.current ? encodeSubscribeRef.current(room) : room;
    const toUnsub = (room: string) =>
      encodeUnsubscribeRef.current ? encodeUnsubscribeRef.current(room) : room;
    for (const room of wanted) active.subscribe(toSub(room));
    return () => {
      for (const room of wanted) active.unsubscribe(toUnsub(room));
      stopMessages();
      stopStatus();
      if (ownsClient) active.stop();
    };
  }, [enabled, client, config, roomsKey, debounceMs]);

  return { status: enabled ? status : "idle" };
}
