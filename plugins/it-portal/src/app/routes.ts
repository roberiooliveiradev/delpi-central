export const IT_PORTAL_BASE_PATH = "/apps/it-portal";

export type PluginView = "home" | "servers" | "server_detail" | "action_plans" | "help" | "not_found";

export type NavId = "home" | "servers" | "action_plans" | "help";

export type ResolvedRoute = { view: PluginView; serverId?: string };

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function normalizePathname(pathname: string): string {
  const trimmed = pathname.split("?")[0].replace(/\/+$/, "");
  return trimmed || "/";
}

export function normalizeBasePath(basePath?: string): string {
  return normalizePathname(basePath || IT_PORTAL_BASE_PATH);
}

export function resolveRoute(pathname: string, basePath: string): ResolvedRoute {
  const current = normalizePathname(pathname);
  if (current !== basePath && !current.startsWith(`${basePath}/`)) return { view: "not_found" };
  const segments = current.slice(basePath.length).split("/").filter(Boolean);
  if (segments.length === 0) return { view: "home" };
  if (segments[0] === "servers") {
    if (segments.length === 1) return { view: "servers" };
    if (segments.length === 2 && UUID_PATTERN.test(segments[1])) {
      return { view: "server_detail", serverId: segments[1].toLowerCase() };
    }
    return { view: "not_found" };
  }
  if (segments.length === 1 && segments[0] === "action-plans") return { view: "action_plans" };
  if (segments.length === 1 && segments[0] === "help") return { view: "help" };
  return { view: "not_found" };
}

export function activeNavId(view: PluginView): NavId | null {
  if (view === "server_detail") return "servers";
  if (view === "not_found") return null;
  return view;
}

const NAV_SEGMENTS: Record<NavId, string> = {
  home: "",
  servers: "/servers",
  action_plans: "/action-plans",
  help: "/help",
};

export function buildPath(basePath: string, target: NavId | { serverId: string }): string {
  if (typeof target === "object") return `${basePath}/servers/${target.serverId}`;
  return `${basePath}${NAV_SEGMENTS[target]}` || "/";
}
