function readCurrentPath(): string {
  if (typeof window === "undefined") return "";
  return `${window.location.pathname}${window.location.search}`;
}

export function navigateProductionPulse(path: string): void {
  if (typeof window === "undefined") return;
  if (readCurrentPath() === path) return;

  window.history.pushState(null, "", path);
  const popState =
    typeof PopStateEvent === "function"
      ? new PopStateEvent("popstate")
      : new Event("popstate");
  window.dispatchEvent(popState);
}

export function replaceProductionPulse(path: string): void {
  if (typeof window === "undefined") return;
  if (readCurrentPath() === path) return;

  window.history.replaceState(null, "", path);
  const popState =
    typeof PopStateEvent === "function"
      ? new PopStateEvent("popstate")
      : new Event("popstate");
  window.dispatchEvent(popState);
}
