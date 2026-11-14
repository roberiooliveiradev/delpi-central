import type { RouteItem } from "../data/coreApi";
import { normalizeRequiredPermissions } from "./routePermission";

function normalizePath(path: string): string {
  const trimmed = path.trim();
  if (!trimmed) return "/";
  return trimmed.replace(/\/+$/, "") || "/";
}

export type ResolvedRoutePermission = {
  /** Códigos exigidos (ANY-OF). Vazio = rota sem gate de permission. */
  required: string[];
  /** Código primário (compat / deep-link state). */
  permission?: string;
  anyOfPermissions?: string[];
};

/**
 * Resolve a(s) permissão(ões) RBAC do manifesto para o pathname atual.
 * Rotas mais específicas (path mais longo) têm precedência.
 * Com `anyOfPermissions`, a exigência é ANY-OF.
 */
export function resolveManifestRoutePermission(
  routes: RouteItem[] | undefined,
  pathname: string,
  fallbackPermission?: string | null,
): string | undefined {
  return resolveManifestRouteAccess(routes, pathname, fallbackPermission).permission;
}

export function resolveManifestRouteAccess(
  routes: RouteItem[] | undefined,
  pathname: string,
  fallbackPermission?: string | null,
): ResolvedRoutePermission {
  const current = normalizePath(pathname);

  const candidates = (routes ?? [])
    .filter((route) => route.path)
    .map((route) => ({
      route,
      path: normalizePath(route.path),
      required: normalizeRequiredPermissions(
        route.permission,
        route.anyOfPermissions,
      ),
    }))
    .filter(
      ({ path, required }) =>
        required.length > 0 &&
        (current === path || current.startsWith(`${path}/`)),
    )
    .sort((a, b) => b.path.length - a.path.length);

  const best = candidates[0];
  if (best) {
    return {
      required: best.required,
      permission: best.required[0],
      anyOfPermissions:
        best.required.length >= 2 ? [...best.required] : undefined,
    };
  }

  const fallback = String(fallbackPermission || "").trim();
  if (fallback) {
    return { required: [fallback], permission: fallback };
  }
  return { required: [] };
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
