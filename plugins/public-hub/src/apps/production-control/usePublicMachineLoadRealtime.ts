import { useEffect, useRef, useState } from "react";
import { buildPublicMachineLoadWsUrl } from "./api";

const PING_MS = 25_000;
const RECONNECT_MS = 5_000;

type Options = {
  token: string;
  branch: string;
  onChanged: (reason: string) => void;
};

/**
 * Escuta mudanças estruturais da fila (reordenação e refresh TOTVS pelo PCP).
 * Status de apontamento (em produção / já apontada) não passa por este canal —
 * o cockpit faz polling HTTP periódico com enrich ao vivo.
 */
export function usePublicMachineLoadRealtime({ token, branch, onChanged }: Options): boolean {
  const [connected, setConnected] = useState(false);
  const onChangedRef = useRef(onChanged);
  onChangedRef.current = onChanged;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let pingTimer = 0;
    let reconnectTimer = 0;
    let disposed = false;

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
        pingTimer = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) socket.send("ping");
        }, PING_MS);
      };

      socket.onmessage = (event) => {
        let message: { type?: string; reason?: string };
        try {
          message = JSON.parse(String(event.data)) as { type?: string; reason?: string };
        } catch {
          return;
        }
        if (message.type === "machine_load_updated") {
          onChangedRef.current(message.reason || "update");
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
