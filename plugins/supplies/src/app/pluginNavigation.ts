import {
  buildPluginPath,
  buildUserProfileHref,
  normalizePathname,
  type PluginRoutableView,
} from "./pluginRoutes";

export function navigatePluginPath(
  target: string,
  options?: { replace?: boolean },
): void {
  if (typeof window === "undefined") return;

  const current = `${normalizePathname(window.location.pathname)}${window.location.search || ""}`;
  if (current === target) return;

  if (options?.replace) {
    window.history.replaceState(null, "", target);
  } else {
    window.history.pushState(null, "", target);
  }
  const popState =
    typeof PopStateEvent === "function"
      ? new PopStateEvent("popstate")
      : new Event("popstate");
  window.dispatchEvent(popState);
}

export function navigatePluginView(
  view: PluginRoutableView,
  options?: { basePath?: string; search?: string; replace?: boolean },
): void {
  const target = buildPluginPath(view, options?.basePath, options?.search);
  navigatePluginPath(target, { replace: options?.replace });
}

export function navigateUserProfile(
  userId: string,
  options?: { basePath?: string; search?: string; replace?: boolean },
): void {
  const target = buildUserProfileHref(userId, options?.basePath, options?.search);
  navigatePluginPath(target, { replace: options?.replace });
}
