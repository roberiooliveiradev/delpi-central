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

/**
 * Resolve a rota de entrada autorizada do app quando o usuário chega ao
 * basePath exato sem a permission da rota raiz — mesma convenção do
 * launcher (`visibleRoutes[0]` ?? `routes[0]`): primeira rota visível no
 * menu, senão a primeira autorizada.
 *
 * Só aplica ao basePath exato: rotas internas negadas continuam indo
 * para /unauthorized (a negação é evidência, não se esconde). Retorna
 * `undefined` fora do basePath, sem rotas autorizadas, ou quando a
 * entrada já é o path atual (evita loop de redirect).
 */
export function resolveAuthorizedEntryPath(
  authorizedRoutes: RouteItem[] | undefined,
  pathname: string,
  basePath: string | undefined,
): string | undefined {
  const current = normalizePath(pathname);
  const base = normalizePath(basePath ?? "");
  if (!base || base === "/" || current !== base) return undefined;

  const routes = (authorizedRoutes ?? []).filter((route) => route.path);
  const entry =
    routes.find((route) => route.showInMenu !== false) ?? routes[0];
  if (!entry) return undefined;

  const target = normalizePath(entry.path);
  return target !== current ? target : undefined;
}
