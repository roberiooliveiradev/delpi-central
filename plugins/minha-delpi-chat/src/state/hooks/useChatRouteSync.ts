import { useEffect, useRef } from "react";

import { parseChatRoute, type ChatRoute } from "../../navigation/chatRoutes";
import type { ChatSession } from "../../data/api/chatTypes";

type UseChatRouteSyncOptions = {
  pathname?: string;
  sessions: ChatSession[];
  workspaceReady?: boolean;
  workspaceRevision?: number;
  onApplyRoute: (route: ChatRoute) => void;
};

export function useChatRouteSync({
  pathname,
  sessions,
  workspaceReady = true,
  workspaceRevision = 0,
  onApplyRoute,
}: UseChatRouteSyncOptions) {
  const isApplyingRouteRef = useRef(false);
  const lastAppliedPathnameRef = useRef<string | null>(null);
  const lastAppliedSessionCountRef = useRef<number>(0);
  const lastAppliedWorkspaceReadyRef = useRef<boolean>(workspaceReady);
  const lastAppliedWorkspaceRevisionRef = useRef<number>(workspaceRevision);

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

    const workspaceDataChanged =
      workspaceRevision !== lastAppliedWorkspaceRevisionRef.current;

    if (
      !pathnameChanged &&
      !sessionsGrew &&
      !workspaceBecameReady &&
      !workspaceDataChanged
    ) {
      return;
    }

    if (!workspaceReady) {
      return;
    }

    lastAppliedPathnameRef.current = pathname;
    lastAppliedSessionCountRef.current = sessions.length;
    lastAppliedWorkspaceReadyRef.current = workspaceReady;
    lastAppliedWorkspaceRevisionRef.current = workspaceRevision;

    isApplyingRouteRef.current = true;

    try {
      onApplyRoute(route);
    } finally {
      isApplyingRouteRef.current = false;
    }
  }, [pathname, sessions, workspaceReady, workspaceRevision, onApplyRoute]);

  return { isApplyingRouteRef };
}
