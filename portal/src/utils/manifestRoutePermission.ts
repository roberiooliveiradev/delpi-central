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
 * Entrada multi-público: no basePath exato, o usuário que detém pelo
 * menos uma rota autorizada no app pode montar o MFE — a view de
 * entrada é resolvida pelo próprio app conforme as capabilities do
 * viewer (Home única). A permission da rota raiz não precisa ser
 * compartilhada por todos os públicos: `access` e `access.dre` entram
 * pelo mesmo basePath.
 *
 * Só aplica ao basePath exato: rotas internas negadas continuam indo
 * para /unauthorized (a negação é evidência, não se esconde). Retorna
 * `false` fora do basePath ou sem rotas autorizadas.
 */
export function hasAuthorizedAppEntry(
  authorizedRoutes: RouteItem[] | undefined,
  pathname: string,
  basePath: string | undefined,
): boolean {
  const current = normalizePath(pathname);
  const base = normalizePath(basePath ?? "");
  if (!base || base === "/" || current !== base) return false;

  return (authorizedRoutes ?? []).some((route) => route.path);
}
