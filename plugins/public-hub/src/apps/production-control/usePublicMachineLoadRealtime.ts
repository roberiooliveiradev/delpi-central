import { useEffect, useRef, useState } from "react";
import { buildPublicMachineLoadWsUrl } from "./api";

const PING_MS = 25_000;
const RECONNECT_MS = 5_000;

export type MachineLoadRealtimeEvent = {
  type: "machine_load_updated" | "production_run_updated";
  reason: string;
  branch?: string;
  workCenter?: string;
  runId?: string;
  piecesTotal?: number;
};

type Options = {
  token: string;
  branch: string;
  onChanged: (event: MachineLoadRealtimeEvent) => void;
  onReconnected?: () => void;
};

/**
 * Escuta mudanças estruturais da fila e atualizações do run de produção.
 * O WebSocket é o caminho principal da contagem; o polling HTTP do run fica
 * ativo somente como fallback enquanto a conexão estiver indisponível.
 */
export function usePublicMachineLoadRealtime({
  token,
  branch,
  onChanged,
  onReconnected,
}: Options): boolean {
  const [connected, setConnected] = useState(false);
  const onChangedRef = useRef(onChanged);
  const onReconnectedRef = useRef(onReconnected);
  onChangedRef.current = onChanged;
  onReconnectedRef.current = onReconnected;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let pingTimer = 0;
    let reconnectTimer = 0;
    let disposed = false;
    let hasConnected = false;

    const clearTimers = () => {
      window.clearInterval(pingTimer);
      window.clearTimeout(reconnectTimer);
      pingTimer = 0;
      reconnectTimer = 0;
    };

    const connect = () => {
      if (disposed) return;
      try {
        socket = new WebSocket(buildPublicMachineLoadWsUrl(token, branch));
      } catch {
        reconnectTimer = window.setTimeout(connect, RECONNECT_MS);
        return;
      }

      socket.onopen = () => {
        if (disposed) return;
        setConnected(true);
        if (hasConnected) onReconnectedRef.current?.();
        hasConnected = true;
        pingTimer = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) socket.send("ping");
        }, PING_MS);
      };

      socket.onmessage = (event) => {
        let message: Partial<MachineLoadRealtimeEvent>;
        try {
          message = JSON.parse(String(event.data)) as Partial<MachineLoadRealtimeEvent>;
        } catch {
          return;
        }
        if (message.type === "machine_load_updated" || message.type === "production_run_updated") {
          onChangedRef.current({
            ...message,
            type: message.type,
            reason: message.reason || "update",
          });
        }
      };

      socket.onerror = () => socket?.close();

      socket.onclose = () => {
        setConnected(false);
        window.clearInterval(pingTimer);
        pingTimer = 0;
        if (!disposed) reconnectTimer = window.setTimeout(connect, RECONNECT_MS);
      };
    };

    connect();

    return () => {
      disposed = true;
      clearTimers();
      socket?.close();
      socket = null;
      setConnected(false);
    };
  }, [token, branch]);

  return connected;
}
