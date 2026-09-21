import { useEffect, useState } from "react";

export type HelpdeskRoute =
  | { kind: "list" }
  | { kind: "new" }
  | { kind: "detail"; ticketId: string }
  | { kind: "unknown" };

export function parseHelpdeskRoute(pathname: string): HelpdeskRoute {
  const path = pathname.replace(/\/+$/, "") || "/";
  if (path === "/apps/helpdesk") return { kind: "list" };
  if (path === "/apps/helpdesk/tickets/new") return { kind: "new" };
  const detail = path.match(/^\/apps\/helpdesk\/tickets\/(\d+)$/);
  if (detail) return { kind: "detail", ticketId: detail[1] };
  if (path.startsWith("/apps/helpdesk")) return { kind: "unknown" };
  return { kind: "unknown" };
}

export function useHelpdeskRouterPath(pathnameFromHost?: string) {
  const [pathname, setPathname] = useState(
    () => pathnameFromHost || (typeof window === "undefined" ? "/apps/helpdesk" : window.location.pathname),
  );

  useEffect(() => {
    if (pathnameFromHost) {
      setPathname(pathnameFromHost);
      return;
    }
    const onPop = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [pathnameFromHost]);

  return pathname;
}

export function navigateHelpdesk(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function ticketDetailPath(ticketId: number | string): string {
  return `/apps/helpdesk/tickets/${ticketId}`;
}

export function isModifiedHelpdeskClick(event: {
  metaKey: boolean;
  ctrlKey: boolean;
  shiftKey: boolean;
  altKey: boolean;
  button?: number;
}): boolean {
  return event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button === 1;
}

export function followHelpdeskPath(
  path: string,
  event?: { metaKey: boolean; ctrlKey: boolean; shiftKey: boolean; altKey: boolean; button?: number },
) {
  if (typeof window === "undefined") return;
  if (event && isModifiedHelpdeskClick(event)) {
    window.open(path, "_blank", "noopener");
    return;
  }
  navigateHelpdesk(path);
}
