import type { RouteItem } from "../data/coreApi";

function normalizePath(path: string): string {
  const trimmed = path.trim();
  if (!trimmed) return "/";
  return trimmed.replace(/\/+$/, "") || "/";
}

/**
 * Resolve a permissão RBAC do manifesto para o pathname atual.
 * Rotas mais específicas (path mais longo) têm precedência.
 */
export function resolveManifestRoutePermission(
  routes: RouteItem[] | undefined,
  pathname: string,
  fallbackPermission?: string | null,
): string | undefined {
  const current = normalizePath(pathname);

  const candidates = (routes ?? [])
    .filter((route) => route.permission && route.path)
    .map((route) => ({
      permission: route.permission!,
      path: normalizePath(route.path),
    }))
    .filter(({ path }) => current === path || current.startsWith(`${path}/`))
    .sort((a, b) => b.path.length - a.path.length);

  return candidates[0]?.permission ?? fallbackPermission ?? undefined;
}
