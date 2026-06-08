import type { MouseEvent } from "react";

import { parseChatRoute, type ChatRoute } from "./chatRoutes";

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
 */
export function navigateChatSurface(
  href: string,
  options: {
    replace?: boolean;
    onApplyRoute?: (route: ChatRoute) => void;
  } = {},
) {
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
