export const IT_PORTAL_BASE_PATH = "/apps/it-portal";

export type PluginView =
  | "home"
  | "servers"
  | "server_detail"
  | "services"
  | "service_detail"
  | "databases"
  | "database_detail"
  | "action_plans"
  | "help"
  | "not_found";

export type NavId = "home" | "servers" | "services" | "databases" | "action_plans" | "help";

export type ResolvedRoute = { view: PluginView; serverId?: string; serviceId?: string; databaseId?: string };

export type DetailTarget = { serverId: string } | { serviceId: string } | { databaseId: string };

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Coleções com página de detalhe `/<segmento>/<uuid>`. */
const COLLECTIONS = {
  servers: { list: "servers", detail: "server_detail", idKey: "serverId" },
  services: { list: "services", detail: "service_detail", idKey: "serviceId" },
  databases: { list: "databases", detail: "database_detail", idKey: "databaseId" },
} as const satisfies Record<string, { list: PluginView; detail: PluginView; idKey: keyof ResolvedRoute }>;

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
  const collection = COLLECTIONS[segments[0] as keyof typeof COLLECTIONS];
  if (collection) {
    if (segments.length === 1) return { view: collection.list };
    if (segments.length === 2 && UUID_PATTERN.test(segments[1])) {
      return { view: collection.detail, [collection.idKey]: segments[1].toLowerCase() };
    }
    return { view: "not_found" };
  }
  if (segments.length === 1 && segments[0] === "action-plans") return { view: "action_plans" };
  if (segments.length === 1 && segments[0] === "help") return { view: "help" };
  return { view: "not_found" };
}

export function activeNavId(view: PluginView): NavId | null {
  if (view === "server_detail") return "servers";
  if (view === "service_detail") return "services";
  if (view === "database_detail") return "databases";
  if (view === "not_found") return null;
  return view;
}

const NAV_SEGMENTS: Record<NavId, string> = {
  home: "",
  servers: "/servers",
  services: "/services",
  databases: "/databases",
  action_plans: "/action-plans",
  help: "/help",
};

export function buildPath(basePath: string, target: NavId | DetailTarget): string {
  if (typeof target === "object") {
    if ("serverId" in target) return `${basePath}/servers/${target.serverId}`;
    if ("serviceId" in target) return `${basePath}/services/${target.serviceId}`;
    return `${basePath}/databases/${target.databaseId}`;
  }
  return `${basePath}${NAV_SEGMENTS[target]}` || "/";
}
