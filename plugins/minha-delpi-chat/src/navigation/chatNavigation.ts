import type { MouseEvent } from "react";

import { parseChatRoute, type ChatRoute } from "./chatRoutes";

/**
 * `portal` — pushState/popstate no AppHost (MFE completo).
 * `embedded` — sem mutar a URL do host (ex.: sidebar TV Copiloto em /apps/tv-dashboard/…).
 */
export type ChatNavigationHostMode = "portal" | "embedded";

let navigationHostMode: ChatNavigationHostMode = "portal";

export function getChatNavigationHostMode(): ChatNavigationHostMode {
  return navigationHostMode;
}

export function setChatNavigationHostMode(mode: ChatNavigationHostMode): void {
  navigationHostMode = mode;
}

export function shouldOpenChatLinkInNewTab(event: Pick<
  MouseEvent,
  "button" | "metaKey" | "ctrlKey" | "shiftKey" | "altKey" | "defaultPrevented"
>) {
  if (event.defaultPrevented) {
    return true;
  }

  return (
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey
  );
}

export function resolveChatLocation(href?: string) {
  if (typeof window === "undefined") {
    return href ?? "";
  }

  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
}

export function navigateChatHref(href: string, options: { replace?: boolean } = {}) {
  if (typeof window === "undefined") {
    return false;
  }

  /* Embarcado: nunca pushState — senão o portal troca para o MFE do chat. */
  if (navigationHostMode === "embedded") {
    return false;
  }

  const current = resolveChatLocation();

  if (current === href) {
    return false;
  }

  if (options.replace) {
    window.history.replaceState(window.history.state, "", href);
  } else {
    window.history.pushState(window.history.state, "", href);
  }

  window.dispatchEvent(new PopStateEvent("popstate"));
  return true;
}

/**
 * Navega para uma superfície do chat e reaplica a rota quando a URL já é a mesma
 * (ex.: «Nova conversa» no chat comum já aberto).
 * Em modo embedded, sempre aplica via onApplyRoute (URL do host permanece).
 */
export function navigateChatSurface(
  href: string,
  options: {
    replace?: boolean;
    onApplyRoute?: (route: ChatRoute) => void;
  } = {},
) {
  if (navigationHostMode === "embedded") {
    options.onApplyRoute?.(parseChatRoute(href));
    return;
  }

  const navigated = navigateChatHref(href, { replace: options.replace });

  if (!navigated && options.onApplyRoute) {
    options.onApplyRoute(parseChatRoute(href));
  }
}

export function handleChatNavClick(
  event: MouseEvent<HTMLAnchorElement>,
  href: string,
  options: {
    replace?: boolean;
    onNavigate?: () => void;
    onApplyRoute?: (route: ChatRoute) => void;
  } = {},
) {
  if (shouldOpenChatLinkInNewTab(event)) {
    return;
  }

  event.preventDefault();
  navigateChatSurface(href, {
    replace: options.replace,
    onApplyRoute: options.onApplyRoute,
  });
  options.onNavigate?.();
}
