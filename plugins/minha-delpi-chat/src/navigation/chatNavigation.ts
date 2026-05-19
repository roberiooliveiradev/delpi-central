import type { MouseEvent } from "react";

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

export function handleChatNavClick(
  event: MouseEvent<HTMLAnchorElement>,
  href: string,
  options: { replace?: boolean; onNavigate?: () => void } = {},
) {
  if (shouldOpenChatLinkInNewTab(event)) {
    return;
  }

  event.preventDefault();
  navigateChatHref(href, options);
  options.onNavigate?.();
}

export function navigateChatHref(href: string, options: { replace?: boolean } = {}) {
  if (typeof window === "undefined") {
    return;
  }

  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;

  if (current === href) {
    return;
  }

  if (options.replace) {
    window.history.replaceState(window.history.state, "", href);
  } else {
    window.history.pushState(window.history.state, "", href);
  }

  window.dispatchEvent(new PopStateEvent("popstate"));
}
