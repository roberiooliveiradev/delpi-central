/** Base path canônico do plugin (manifest / Portal). */
export const CONTROLLERSHIP_FINANCE_BASE_PATH = "/apps/controllership-finance";

/**
 * IMP-MFE-HOME: somente a rota Início existe em runtime.
 * Rotas futuras (Visão geral, Sala de interação, Minhas tarefas,
 * Administração, Ajuda) entram aqui apenas quando implementadas.
 */
export type PluginView = "home" | "not_found";

export type PluginNavId = "home";

export type PluginNavigationTarget = "home";

export type ResolvedPluginRoute = {
  view: PluginView;
  pathname: string;
  relativePath: string;
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
  return normalizePathname(basePath?.trim() || CONTROLLERSHIP_FINANCE_BASE_PATH);
}

export function resolvePluginRoute(
  pathname: string | undefined,
  basePath?: string,
): ResolvedPluginRoute {
  const base = normalizeBasePath(basePath);
  const path = normalizePathname(pathname ?? base);

  if (path === base) {
    return { view: "home", pathname: path, relativePath: "" };
  }

  return { view: "not_found", pathname: path, relativePath: path.slice(base.length) };
}

/** Path canônico da view (paths só via buildPluginPath — sem URL absoluta). */
export function buildPluginPath(
  view: PluginNavigationTarget,
  basePath?: string,
  search?: string,
): string {
  const base = normalizeBasePath(basePath);
  const suffix = view === "home" ? "" : "";
  const normalizedSearch = search?.startsWith("?")
    ? search
    : search
      ? `?${search}`
      : "";
  return `${base}${suffix}${normalizedSearch}`;
}

export function resolveActiveNavId(view: PluginView): PluginNavId | null {
  if (view === "home") return "home";
  return null;
}
