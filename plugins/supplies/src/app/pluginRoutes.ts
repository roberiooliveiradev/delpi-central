/** Base path canônico do plugin (manifest / Portal). */
export const SUPPLIES_BASE_PATH = "/apps/supplies";

export type PluginView =
  | "home"
  | "overview"
  | "my_tasks"
  | "purchase_requests"
  | "purchase_orders"
  | "deliveries"
  | "suppliers"
  | "products"
  | "inventory"
  | "safety_stock"
  | "negotiations"
  | "indicators"
  | "administration"
  | "help"
  | "user_profile"
  | "forbidden"
  | "not_found";

export type PluginNavId =
  | "home"
  | "overview"
  | "my_tasks"
  | "purchase_requests"
  | "operations"
  | "administration"
  | "help";

export type PluginNavigationTarget = Exclude<PluginView, "forbidden" | "not_found">;

/** Views navegáveis pelo shell/hub (perfil usa buildUserProfileHref). */
export type PluginRoutableView = Exclude<PluginNavigationTarget, "user_profile">;

export type ResolvedPluginRoute = {
  view: PluginView;
  pathname: string;
  relativePath: string;
  userId?: string;
};

export function normalizePathname(pathname: string): string {
  const raw = (pathname || "").trim() || "/";
  const withoutQuery = raw.split("?")[0]?.split("#")[0] ?? raw;
  if (withoutQuery.length > 1 && withoutQuery.endsWith("/")) {
    return withoutQuery.slice(0, -1);
  }
  return withoutQuery || "/";
}

export function normalizeBasePath(basePath?: string): string {
  return normalizePathname(basePath?.trim() || SUPPLIES_BASE_PATH);
}

const RELATIVE_TO_VIEW: Record<string, PluginView> = {
  overview: "overview",
  "my-tasks": "my_tasks",
  "purchase-requests": "purchase_requests",
  "purchase-orders": "purchase_orders",
  deliveries: "deliveries",
  suppliers: "suppliers",
  products: "products",
  inventory: "inventory",
  "safety-stock": "safety_stock",
  negotiations: "negotiations",
  indicators: "indicators",
  administration: "administration",
  help: "help",
};

export const PLUGIN_VIEW_RELATIVE_PATHS: Record<PluginRoutableView, string> = {
  home: "",
  overview: "overview",
  my_tasks: "my-tasks",
  purchase_requests: "purchase-requests",
  purchase_orders: "purchase-orders",
  deliveries: "deliveries",
  suppliers: "suppliers",
  products: "products",
  inventory: "inventory",
  safety_stock: "safety-stock",
  negotiations: "negotiations",
  indicators: "indicators",
  administration: "administration",
  help: "help",
};

export function resolvePluginRoute(
  pathname: string | undefined,
  basePath?: string,
): ResolvedPluginRoute {
  const base = normalizeBasePath(basePath);
  const path = normalizePathname(pathname ?? base);

  if (path === base) {
    return { view: "home", pathname: path, relativePath: "" };
  }

  if (!path.startsWith(`${base}/`)) {
    return { view: "not_found", pathname: path, relativePath: path };
  }

  const relativePath = path.slice(base.length + 1);
  const userMatch = /^users\/([^/]+)$/.exec(relativePath);
  if (userMatch?.[1]) {
    return {
      view: "user_profile",
      pathname: path,
      relativePath,
      userId: decodeURIComponent(userMatch[1]),
    };
  }
  const view = RELATIVE_TO_VIEW[relativePath];
  if (!view) {
    return { view: "not_found", pathname: path, relativePath };
  }
  return { view, pathname: path, relativePath };
}

export function buildUserProfileHref(
  userId: string,
  basePath?: string,
  search?: string,
): string {
  const base = normalizeBasePath(basePath);
  const path = `${base}/users/${encodeURIComponent(userId)}`;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  if (normalizedSearch === "?") return path;
  return `${path}${normalizedSearch}`;
}

export function buildPluginPath(
  view: PluginRoutableView,
  basePath?: string,
  search?: string,
): string {
  const base = normalizeBasePath(basePath);
  const relative = PLUGIN_VIEW_RELATIVE_PATHS[view] ?? "";
  const path = relative ? `${base}/${relative}` : base;
  if (!search) return path;
  const normalizedSearch = search.startsWith("?") ? search : `?${search}`;
  if (normalizedSearch === "?") return path;
  return `${path}${normalizedSearch}`;
}

export function resolveActiveNavId(view: PluginView): PluginNavId | null {
  switch (view) {
    case "home":
      return "home";
    case "overview":
    case "negotiations":
    case "indicators":
      return "overview";
    case "my_tasks":
      return "my_tasks";
    case "purchase_requests":
      return "purchase_requests";
    case "purchase_orders":
    case "deliveries":
    case "suppliers":
    case "products":
    case "inventory":
    case "safety_stock":
      return "operations";
    case "administration":
      return "administration";
    case "help":
      return "help";
    case "user_profile":
      return null;
    default:
      return null;
  }
}
