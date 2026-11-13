import { RealtimeSocketClient } from "@delpi/plugin-ui/index";
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { peekAccessToken } from "../data/api/httpClient";
import {
  buildLnfRealtimeWsUrl,
  shouldConnectLnfRealtime,
  shouldReconnectLnfRealtime,
} from "./config";
import { parseLnfControlMessage } from "./events";

type RealtimeConnectionStatus =
  | "idle"
  | "connecting"
  | "open"
  | "reconnecting"
  | "unavailable"
  | "closed";

type LnfRealtimeClient = {
  start: () => void;
  stop: () => void;
  getStatus: () => RealtimeConnectionStatus;
  onStatusChange: (
    listener: (status: RealtimeConnectionStatus) => void,
  ) => () => void;
  addMessageListener: (listener: (raw: string) => void) => () => void;
};

type LnfRealtimeContextValue = {
  enabled: boolean;
  client: LnfRealtimeClient | null;
  status: RealtimeConnectionStatus;
  /** Sala com forbidden_room mais recente (sem erro visível na UI). */
  lastForbiddenRoom: string | null;
};

const LnfRealtimeContext = createContext<LnfRealtimeContextValue>({
  enabled: false,
  client: null,
  status: "idle",
  lastForbiddenRoom: null,
});

type Props = {
  getAccessToken?: () => string | undefined;
  children: ReactNode;
};

export function LnfRealtimeProvider({ getAccessToken, children }: Props) {
  const enabled = shouldConnectLnfRealtime();
  const getAccessTokenRef = useRef(getAccessToken);
  getAccessTokenRef.current = getAccessToken;
  const [status, setStatus] = useState<RealtimeConnectionStatus>("idle");
  const [lastForbiddenRoom, setLastForbiddenRoom] = useState<string | null>(
    null,
  );

  const client = useMemo((): LnfRealtimeClient | null => {
    if (!enabled) return null;
    return new RealtimeSocketClient({
      buildUrl: () => {
        const token =
          getAccessTokenRef.current?.() ?? peekAccessToken() ?? undefined;
        if (!token) return null;
        return buildLnfRealtimeWsUrl(token);
      },
      resolveUrl: () => {
        const token =
          getAccessTokenRef.current?.() ?? peekAccessToken() ?? undefined;
        if (!token) return null;
        return buildLnfRealtimeWsUrl(token);
      },
      reconnect: {
        mode: "exponential",
        baseMs: 1_000,
        maxMs: 30_000,
        jitter: true,
      },
      resubscribeOnReconnect: true,
      shouldReconnect: shouldReconnectLnfRealtime,
      onMessage: () => undefined,
    }) as unknown as LnfRealtimeClient;
  }, [enabled]);

  useEffect(() => {
    if (!client) {
      setStatus("idle");
      setLastForbiddenRoom(null);
      return;
    }
    const stopStatus = client.onStatusChange(setStatus);
    const stopMessages = client.addMessageListener((raw: string) => {
      const msg = parseLnfControlMessage(raw);
      if (msg && msg.type === "error" && msg.code === "forbidden_room") {
        setLastForbiddenRoom(typeof msg.room === "string" ? msg.room : "");
      }
    });
    client.start();
    setStatus(client.getStatus());
    return () => {
      stopMessages();
      stopStatus();
      client.stop();
    };
  }, [client]);

  const value = useMemo(
    () => ({ enabled, client, status, lastForbiddenRoom }),
    [enabled, client, status, lastForbiddenRoom],
  );

  return (
    <LnfRealtimeContext.Provider value={value}>
      {children}
    </LnfRealtimeContext.Provider>
  );
}

export function useLnfRealtime(): LnfRealtimeContextValue {
  return useContext(LnfRealtimeContext);
}
