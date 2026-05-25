import { useEffect, useRef } from "react";

import { parseChatRoute, type ChatRoute } from "../../navigation/chatRoutes";
import type { ChatSession } from "../../data/api/chatTypes";

type UseChatRouteSyncOptions = {
  pathname?: string;
  sessions: ChatSession[];
  onApplyRoute: (route: ChatRoute) => void;
};

export function useChatRouteSync({
  pathname,
  sessions,
  onApplyRoute,
}: UseChatRouteSyncOptions) {
  const isApplyingRouteRef = useRef(false);
  const lastAppliedPathnameRef = useRef<string | null>(null);
  const lastAppliedSessionCountRef = useRef<number>(0);

  useEffect(() => {
    if (!pathname) {
      return;
    }

    const pathnameChanged = pathname !== lastAppliedPathnameRef.current;
    const route = parseChatRoute(pathname);

    const sessionsGrew =
      route.kind === "session" &&
      sessions.length > lastAppliedSessionCountRef.current;

    if (!pathnameChanged && !sessionsGrew) {
      return;
    }

    lastAppliedPathnameRef.current = pathname;
    lastAppliedSessionCountRef.current = sessions.length;

    isApplyingRouteRef.current = true;

    try {
      onApplyRoute(route);
    } finally {
      isApplyingRouteRef.current = false;
    }
  }, [pathname, sessions, onApplyRoute]);

  return { isApplyingRouteRef };
}
