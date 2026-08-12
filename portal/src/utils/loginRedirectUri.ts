/**
 * URI de retorno do Keycloak após login / reauth.
 * Preserva deep links (/apps/..., /admin/...) para F5 e 401 não jogarem o usuário na home.
 */
export function resolveLoginRedirectUri(options: {
  origin: string;
  pathname: string;
  search?: string;
  /** Fallback só quando a rota atual é /login (ou vazia). */
  configuredFallback?: string | null;
}): string {
  const pathname = (options.pathname || "/").trim() || "/";
  const search = options.search ?? "";

  if (pathname !== "/login") {
    return `${options.origin}${pathname}${search}`;
  }

  const fallback = options.configuredFallback?.trim();
  if (fallback) return fallback;
  return `${options.origin}/`;
}
