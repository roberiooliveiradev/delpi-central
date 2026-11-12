/** ENG-REALTIME-01 — provider de tempo real do Portal Engenharia.
 *
 * Uma conexão `/apps/engineering-api/v1/realtime/ws` por MFE; fila e
 * detalhe PRC assinam via `subscribeChanged`/`joinCase`. Eventos só
 * invalidam — o refetch usa os clients HTTP oficiais (AuthZ backend).
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  ENGINEERING_PRC_DOMAIN,
  RealtimeSocketClient,
  buildEngineeringRealtimeWsUrl,
  buildEngineeringSubscribePayload,
  buildEngineeringUnsubscribePayload,
  parseEngineeringRealtimeMessage,
  type EngineeringResourceChangedEvent,
} from "@delpi/plugin-ui/index";

import { getEngineeringClientId } from "./engineeringClientId";

const SYNC_DEBOUNCE_MS = 400;
const ENGINEERING_API_BASE = "/apps/engineering-api";

type ChangedHandler = (event: EngineeringResourceChangedEvent) => void;

type EngineeringRealtimeContextValue = {
  connected: boolean;
  subscribeChanged: (handler: ChangedHandler) => () => void;
  joinCase: (requestId: string) => void;
  leaveCase: (requestId: string) => void;
};

const EngineeringRealtimeContext =
  createContext<EngineeringRealtimeContextValue | null>(null);

type Props = {
  getAccessToken?: () => string | undefined;
  enabled?: boolean;
  children: ReactNode;
};

export function EngineeringRealtimeProvider({
  getAccessToken,
  enabled = true,
  children,
}: Props) {
  const clientIdRef = useRef(getEngineeringClientId());
  const socketRef = useRef<RealtimeSocketClient | null>(null);
  const handlersRef = useRef(new Set<ChangedHandler>());
  const desiredCasesRef = useRef(new Set<string>());
  const getAccessTokenRef = useRef(getAccessToken);

  const [connected, setConnected] = useState(false);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const joinCase = useCallback((requestId: string) => {
    const id = requestId.trim();
    if (!id) return;
    desiredCasesRef.current.add(id);
    socketRef.current?.subscribe(
      buildEngineeringSubscribePayload(ENGINEERING_PRC_DOMAIN, id),
    );
  }, []);

  const leaveCase = useCallback((requestId: string) => {
    const id = requestId.trim();
    if (!id) return;
    desiredCasesRef.current.delete(id);
    socketRef.current?.unsubscribe(
      buildEngineeringUnsubscribePayload(ENGINEERING_PRC_DOMAIN, id),
    );
  }, []);

  const subscribeChanged = useCallback((handler: ChangedHandler) => {
    handlersRef.current.add(handler);
    return () => {
      handlersRef.current.delete(handler);
    };
  }, []);

  useEffect(() => {
    if (!enabled) {
      socketRef.current?.stop();
      socketRef.current = null;
      setConnected(false);
      return;
    }
    const client = new RealtimeSocketClient({
      buildUrl: () => {
        const token = getAccessTokenRef.current?.();
        if (!token) return null;
        return buildEngineeringRealtimeWsUrl({
          apiBase: ENGINEERING_API_BASE,
          token,
          clientId: clientIdRef.current,
        });
      },
      onMessage: (raw) => {
        const msg = parseEngineeringRealtimeMessage(raw);
        if (
          msg &&
          (msg as { type?: string }).type === "engineering.resource.changed"
        ) {
          const event = msg as EngineeringResourceChangedEvent;
          for (const handler of handlersRef.current) handler(event);
        }
      },
      onStateChange: (state) => setConnected(state.connected),
    });
    socketRef.current = client;
    client.start();
    return () => {
      client.stop();
      socketRef.current = null;
    };
  }, [enabled]);

  const value: EngineeringRealtimeContextValue = {
    connected,
    subscribeChanged,
    joinCase,
    leaveCase,
  };

  return (
    <EngineeringRealtimeContext.Provider value={value}>
      {children}
    </EngineeringRealtimeContext.Provider>
  );
}

export function useEngineeringRealtime(): EngineeringRealtimeContextValue {
  const ctx = useContext(EngineeringRealtimeContext);
  if (!ctx) {
    throw new Error(
      "useEngineeringRealtime must be used within EngineeringRealtimeProvider",
    );
  }
  return ctx;
}

function useDebouncedEngineeringSync(
  onChanged: () => void,
  enabled: boolean,
  match?: (event: EngineeringResourceChangedEvent) => boolean,
) {
  const { subscribeChanged } = useEngineeringRealtime();
  const onChangedRef = useRef(onChanged);
  useEffect(() => {
    onChangedRef.current = onChanged;
  }, [onChanged]);

  useEffect(() => {
    if (!enabled) return;
    let timer: number | null = null;
    const unsubscribe = subscribeChanged((event) => {
      if (event.domain !== ENGINEERING_PRC_DOMAIN) return;
      if (event.resourceType !== "request") return;
      if (match && !match(event)) return;
      if (timer != null) window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        timer = null;
        onChangedRef.current();
      }, SYNC_DEBOUNCE_MS);
    });
    return () => {
      unsubscribe();
      if (timer != null) window.clearTimeout(timer);
    };
  }, [enabled, match, subscribeChanged]);
}

/** Fila PRC — qualquer mudança de caso reindexa a fila. */
export function usePrcQueueSync(onChanged: () => void, enabled = true) {
  useDebouncedEngineeringSync(onChanged, enabled);
}

/** Detalhe PRC — assina a sala do caso e reage a eventos do próprio id. */
export function usePrcCaseSync(
  requestId: string | null | undefined,
  onChanged: () => void,
  enabled = true,
) {
  const { joinCase, leaveCase } = useEngineeringRealtime();
  const id = (requestId || "").trim();

  useEffect(() => {
    if (!enabled || !id) return;
    joinCase(id);
    return () => leaveCase(id);
  }, [enabled, id, joinCase, leaveCase]);

  useDebouncedEngineeringSync(
    onChanged,
    enabled && Boolean(id),
    useCallback(
      (event: EngineeringResourceChangedEvent) =>
        (event.resourceId || "").trim() === id,
      [id],
    ),
  );
}
