/** ENG-REALTIME-01 — provider de tempo real PRC (fonte Engineering API).
 *
 * Segunda conexão do MFE: `/apps/engineering-api/v1/realtime/ws`, ao
 * lado do socket Requests (`MyRequestsRealtimeProvider`), que segue
 * intacto para solicitações tradicionais. Eventos só invalidam — o
 * refetch usa `prcApi` na Engineering API oficial (AuthZ backend). */

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

import { getMyRequestsClientId } from "./myRequestsClientId";

const SYNC_DEBOUNCE_MS = 400;
const ENGINEERING_API_BASE = "/apps/engineering-api";

type ChangedHandler = (event: EngineeringResourceChangedEvent) => void;

type PrcRealtimeContextValue = {
  connected: boolean;
  subscribeChanged: (handler: ChangedHandler) => () => void;
  joinCase: (requestId: string) => void;
  leaveCase: (requestId: string) => void;
};

const PrcRealtimeContext = createContext<PrcRealtimeContextValue | null>(
  null,
);

type Props = {
  getAccessToken?: () => string | undefined;
  enabled?: boolean;
  children: ReactNode;
};

export function PrcRealtimeProvider({
  getAccessToken,
  enabled = true,
  children,
}: Props) {
  const clientIdRef = useRef(getMyRequestsClientId());
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

  const value: PrcRealtimeContextValue = {
    connected,
    subscribeChanged,
    joinCase,
    leaveCase,
  };

  return (
    <PrcRealtimeContext.Provider value={value}>
      {children}
    </PrcRealtimeContext.Provider>
  );
}

export function usePrcRealtime(): PrcRealtimeContextValue {
  const ctx = useContext(PrcRealtimeContext);
  if (!ctx) {
    throw new Error(
      "usePrcRealtime must be used within PrcRealtimeProvider",
    );
  }
  return ctx;
}

/** Lista unificada — qualquer mudança PRC reindexa Minhas Solicitações. */
export function usePrcListSync(onChanged: () => void, enabled = true) {
  const { subscribeChanged } = usePrcRealtime();
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
  }, [enabled, subscribeChanged]);
}

/** Acompanhamento do caso — assina a sala do próprio requestId. */
export function usePrcCaseSync(
  requestId: string | null | undefined,
  onChanged: () => void,
  enabled = true,
) {
  const { joinCase, leaveCase, subscribeChanged } = usePrcRealtime();
  const id = (requestId || "").trim();
  const onChangedRef = useRef(onChanged);
  useEffect(() => {
    onChangedRef.current = onChanged;
  }, [onChanged]);

  useEffect(() => {
    if (!enabled || !id) return;
    joinCase(id);
    return () => leaveCase(id);
  }, [enabled, id, joinCase, leaveCase]);

  useEffect(() => {
    if (!enabled || !id) return;
    let timer: number | null = null;
    const unsubscribe = subscribeChanged((event) => {
      if (event.domain !== ENGINEERING_PRC_DOMAIN) return;
      if (event.resourceType !== "request") return;
      if ((event.resourceId || "").trim() !== id) return;
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
  }, [enabled, id, subscribeChanged]);
}
