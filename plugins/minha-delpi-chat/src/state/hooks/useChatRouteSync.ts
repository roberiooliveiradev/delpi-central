import { useEffect, useRef } from "react";

import { parseChatRoute, type ChatRoute } from "../../navigation/chatRoutes";
import type { ChatSession } from "../../data/api/chatTypes";

type UseChatRouteSyncOptions = {
  pathname?: string;
  sessions: ChatSession[];
  agentsReady?: boolean;
  onApplyRoute: (route: ChatRoute) => void;
};

export function useChatRouteSync({
  pathname,
  sessions,
  agentsReady = true,
  onApplyRoute,
}: UseChatRouteSyncOptions) {
  const isApplyingRouteRef = useRef(false);
  const lastAppliedPathnameRef = useRef<string | null>(null);
  const lastAppliedSessionCountRef = useRef<number>(0);
  const lastAppliedAgentsReadyRef = useRef<boolean>(agentsReady);

  useEffect(() => {
    if (!pathname) {
      return;
    }

    const pathnameChanged = pathname !== lastAppliedPathnameRef.current;
    const route = parseChatRoute(pathname);

    const sessionsGrew =
      (route.kind === "session" || route.kind === "agent-session") &&
      sessions.length > lastAppliedSessionCountRef.current;

    const agentsBecameReady = agentsReady && !lastAppliedAgentsReadyRef.current;

    if (!pathnameChanged && !sessionsGrew && !agentsBecameReady) {
      return;
    }

    lastAppliedPathnameRef.current = pathname;
    lastAppliedSessionCountRef.current = sessions.length;
    lastAppliedAgentsReadyRef.current = agentsReady;

    if (!agentsReady) {
      return;
    }

    isApplyingRouteRef.current = true;

    try {
      onApplyRoute(route);
    } finally {
      isApplyingRouteRef.current = false;
    }
  }, [pathname, sessions, agentsReady, onApplyRoute]);

  return { isApplyingRouteRef };
}
