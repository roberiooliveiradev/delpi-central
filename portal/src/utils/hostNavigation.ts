/**
 * Host-shell paths owned by the Portal SPA (not an MFE basePath).
 * Event name must stay in sync with `@delpi/plugin-ui` `navigateHostPath`.
 */

export const DELPI_HOST_NAVIGATE_EVENT = "DELPI_HOST_NAVIGATE";
export const DELPI_HOST_NAVIGATE_HANDLED_EVENT = "DELPI_HOST_NAVIGATE_HANDLED";

export const HOST_SELF_PROFILE_PATH = "/profile";

const HOST_SHELL_EXACT = new Set([
  "/",
  "/profile",
  "/privacy",
  "/privacy-policy",
  "/notifications",
  "/unauthorized",
  "/delpi/products",
  "/delpi/health",
]);

export function isHostShellPath(pathname: string): boolean {
  const path = (pathname || "").trim() || "/";
  if (HOST_SHELL_EXACT.has(path)) return true;
  if (path.startsWith("/admin")) return true;
  if (path.startsWith("/profile/")) return true;
  return false;
}

export type HostNavigateDetail = {
  path: string;
};

export function notifyHostNavigateHandled(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(DELPI_HOST_NAVIGATE_HANDLED_EVENT));
}
