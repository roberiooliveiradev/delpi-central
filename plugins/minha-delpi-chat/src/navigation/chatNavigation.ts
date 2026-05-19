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
