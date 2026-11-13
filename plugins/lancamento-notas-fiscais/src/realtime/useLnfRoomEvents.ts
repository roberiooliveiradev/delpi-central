import { useRealtimeRooms } from "@delpi/plugin-ui/index";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLnfRealtime } from "./LnfRealtimeProvider";
import { encodeLnfSubscribe, encodeLnfUnsubscribe } from "./rooms";

type Options = {
  rooms: string[];
  enabled?: boolean;
  debounceMs?: number;
  onEvents: (events: unknown[]) => void;
  onResync?: () => void;
};

/**
 * Assina salas LNF na conexão única do provider.
 * Se a sala receber forbidden_room, desliga o tempo real nesta superfície
 * sem mostrar erro.
 */
export function useLnfRoomEvents({
  rooms,
  enabled = true,
  debounceMs = 1_000,
  onEvents,
  onResync,
}: Options): { status: ReturnType<typeof useRealtimeRooms>["status"]; muted: boolean } {
  const { enabled: appEnabled, client, lastForbiddenRoom } = useLnfRealtime();
  const [muted, setMuted] = useState(false);
  const roomsKey = rooms.join("\n");
  const roomsRef = useRef(rooms);
  roomsRef.current = rooms;

  useEffect(() => {
    setMuted(false);
  }, [roomsKey]);

  useEffect(() => {
    if (!lastForbiddenRoom) return;
    if (roomsRef.current.includes(lastForbiddenRoom)) {
      setMuted(true);
    }
  }, [lastForbiddenRoom]);

  const active = appEnabled && enabled && !muted && Boolean(client);
  const stableOnEvents = useCallback(
    (events: unknown[]) => onEvents(events),
    [onEvents],
  );
  const stableRooms = useMemo(
    () => (roomsKey ? roomsKey.split("\n") : []),
    [roomsKey],
  );

  const { status } = useRealtimeRooms({
    enabled: active,
    client,
    rooms: stableRooms,
    debounceMs,
    onEvent: stableOnEvents,
    onResync,
    encodeSubscribe: encodeLnfSubscribe,
    encodeUnsubscribe: encodeLnfUnsubscribe,
  });

  return { status: active ? status : "idle", muted };
}
