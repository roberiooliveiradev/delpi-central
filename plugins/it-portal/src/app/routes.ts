export const IT_PORTAL_BASE_PATH = "/apps/it-portal";

export type PluginView =
  | "home"
  | "workstations"
  | "workstation_detail"
  | "servers"
  | "server_detail"
  | "services"
  | "service_detail"
  | "databases"
  | "database_detail"
  | "networks"
  | "network_detail"
  | "integrations"
  | "integration_detail"
  | "action_plans"
  | "help"
  | "not_found";

export type NavId =
  | "home"
  | "workstations"
  | "servers"
  | "services"
  | "databases"
  | "networks"
  | "integrations"
  | "action_plans"
  | "help";

export type ResolvedRoute = {
  view: PluginView;
  serverId?: string;
  workstationId?: string;
  serviceId?: string;
  databaseId?: string;
  networkId?: string;
  integrationId?: string;
};

export type DetailTarget =
  | { serverId: string }
  | { workstationId: string }
  | { serviceId: string }
  | { databaseId: string }
  | { networkId: string }
  | { integrationId: string };

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Coleções com página de detalhe `/<segmento>/<uuid>`. */
const COLLECTIONS = {
  workstations: { list: "workstations", detail: "workstation_detail", idKey: "workstationId" },
  servers: { list: "servers", detail: "server_detail", idKey: "serverId" },
  services: { list: "services", detail: "service_detail", idKey: "serviceId" },
  databases: { list: "databases", detail: "database_detail", idKey: "databaseId" },
  networks: { list: "networks", detail: "network_detail", idKey: "networkId" },
  integrations: { list: "integrations", detail: "integration_detail", idKey: "integrationId" },
} as const satisfies Record<string, { list: PluginView & NavId; detail: PluginView; idKey: keyof ResolvedRoute }>;

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
  if (view === "not_found") return null;
  const owner = Object.values(COLLECTIONS).find((collection) => collection.detail === view);
  return owner ? owner.list : (view as NavId);
}

const NAV_SEGMENTS: Record<NavId, string> = {
  home: "",
  workstations: "/workstations",
  servers: "/servers",
  services: "/services",
  databases: "/databases",
  networks: "/networks",
  integrations: "/integrations",
  action_plans: "/action-plans",
  help: "/help",
};

export function buildPath(basePath: string, target: NavId | DetailTarget): string {
  if (typeof target === "object") {
    const [segment, collection] = Object.entries(COLLECTIONS).find(([, item]) => item.idKey in target)!;
    return `${basePath}/${segment}/${(target as Record<string, string>)[collection.idKey]}`;
  }
  return `${basePath}${NAV_SEGMENTS[target]}` || "/";
}
