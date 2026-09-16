/** Base path canônico do plugin (manifest / Portal). */
export const SUPPLIES_BASE_PATH = "/apps/supplies";

export type PluginView =
  | "home"
  | "overview"
  | "analytics_otd"
  | "my_tasks"
  | "purchase_requests"
  | "purchase_request_detail"
  | "purchase_orders"
  | "purchase_order_detail"
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
export type PluginRoutableView = Exclude<
  PluginNavigationTarget,
  "user_profile" | "purchase_order_detail" | "purchase_request_detail"
>;

export type ResolvedPluginRoute = {
  view: PluginView;
  pathname: string;
  relativePath: string;
  userId?: string;
  branch?: string;
  orderNumber?: string;
  requestNumber?: string;
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
  "analytics/otd": "analytics_otd",
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
  analytics_otd: "analytics/otd",
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
  const prMatch = /^purchase-requests\/([^/]+)\/([^/]+)$/.exec(relativePath);
  if (prMatch?.[1] && prMatch[2]) {
    return {
      view: "purchase_request_detail",
      pathname: path,
      relativePath,
      branch: decodeURIComponent(prMatch[1]),
      requestNumber: decodeURIComponent(prMatch[2]),
    };
  }
  const poMatch = /^purchase-orders\/([^/]+)\/([^/]+)$/.exec(relativePath);
  if (poMatch?.[1] && poMatch[2]) {
    return {
      view: "purchase_order_detail",
      pathname: path,
      relativePath,
      branch: decodeURIComponent(poMatch[1]),
      orderNumber: decodeURIComponent(poMatch[2]),
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

export function buildPurchaseRequestDetailPath(
  branch: string,
  requestNumber: string,
  basePath?: string,
): string {
  const base = normalizeBasePath(basePath);
  return `${base}/purchase-requests/${encodeURIComponent(branch)}/${encodeURIComponent(requestNumber)}`;
}

export function buildPurchaseOrderDetailPath(
  branch: string,
  orderNumber: string,
  basePath?: string,
): string {
  const base = normalizeBasePath(basePath);
  return `${base}/purchase-orders/${encodeURIComponent(branch)}/${encodeURIComponent(orderNumber)}`;
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
    case "analytics_otd":
    case "negotiations":
    case "indicators":
      return "overview";
    case "my_tasks":
      return "my_tasks";
    case "purchase_requests":
    case "purchase_request_detail":
      return "purchase_requests";
    case "purchase_orders":
    case "purchase_order_detail":
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
