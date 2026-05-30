import { useEffect, useRef } from "react";

import { parseChatRoute, type ChatRoute } from "../../navigation/chatRoutes";
import type { ChatSession } from "../../data/api/chatTypes";

type UseChatRouteSyncOptions = {
  pathname?: string;
  sessions: ChatSession[];
  workspaceReady?: boolean;
  onApplyRoute: (route: ChatRoute) => void;
};

export function useChatRouteSync({
  pathname,
  sessions,
  workspaceReady = true,
  onApplyRoute,
}: UseChatRouteSyncOptions) {
  const isApplyingRouteRef = useRef(false);
  const lastAppliedPathnameRef = useRef<string | null>(null);
  const lastAppliedSessionCountRef = useRef<number>(0);
  const lastAppliedWorkspaceReadyRef = useRef<boolean>(workspaceReady);

  useEffect(() => {
    if (!pathname) {
      return;
    }

    const pathnameChanged = pathname !== lastAppliedPathnameRef.current;
    const route = parseChatRoute(pathname);

    const sessionsGrew =
      (route.kind === "session" ||
        route.kind === "agent-session" ||
        route.kind === "project-session") &&
      sessions.length > lastAppliedSessionCountRef.current;

    const workspaceBecameReady =
      workspaceReady && !lastAppliedWorkspaceReadyRef.current;

    if (!pathnameChanged && !sessionsGrew && !workspaceBecameReady) {
      return;
    }

    lastAppliedPathnameRef.current = pathname;
    lastAppliedSessionCountRef.current = sessions.length;
    lastAppliedWorkspaceReadyRef.current = workspaceReady;

    if (!workspaceReady) {
      return;
    }

    isApplyingRouteRef.current = true;

    try {
      onApplyRoute(route);
    } finally {
      isApplyingRouteRef.current = false;
    }
  }, [pathname, sessions, workspaceReady, onApplyRoute]);

  return { isApplyingRouteRef };
}
