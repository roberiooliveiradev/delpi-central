/** Rotas internas do MFE — sub-paths de `/apps/engineering` resolvidos
 * pelo Portal via maior-prefixo na rota declarada do manifest. Nenhuma
 * rota nova exige alteração de manifest (resolveMatchingRoute cobre
 * aninhadas). */

export const ENGINEERING_BASE_PATH = "/apps/engineering";

export type EngineeringView = "home" | "overview" | "lmps" | "help";

export type ResolvedEngineeringRoute = {
  view: EngineeringView | "not_found";
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

export function normalizeEngineeringBasePath(basePath?: string): string {
  return normalizePathname(basePath?.trim() || ENGINEERING_BASE_PATH);
}

export function resolveEngineeringRoute(
  pathname: string | undefined,
  basePath?: string,
): ResolvedEngineeringRoute {
  const base = normalizeEngineeringBasePath(basePath);
  const path = normalizePathname(pathname ?? base);

  if (path === base) {
    return { view: "home", pathname: path, relativePath: "" };
  }

  if (!path.startsWith(`${base}/`)) {
    return { view: "not_found", pathname: path, relativePath: path };
  }

  const relativePath = path.slice(base.length + 1);

  if (relativePath === "overview") {
    return { view: "overview", pathname: path, relativePath };
  }
  if (relativePath === "lmps" || relativePath.startsWith("lmps/")) {
    return { view: "lmps", pathname: path, relativePath };
  }
  if (relativePath === "help") {
    return { view: "help", pathname: path, relativePath };
  }

  return { view: "not_found", pathname: path, relativePath };
}

export function buildEngineeringPath(
  view: EngineeringView,
  basePath?: string,
): string {
  const base = normalizeEngineeringBasePath(basePath);
  if (view === "home") return base;
  return `${base}/${view}`;
}

/** Navegação interna pelo host — `pushState` + evento que o Portal já
 * observa (mesmo mecanismo usado pelos outros MFEs). */
export function navigateEngineeringView(
  view: EngineeringView,
  options?: { basePath?: string; replace?: boolean },
): void {
  if (typeof window === "undefined") return;
  const href = buildEngineeringPath(view, options?.basePath);
  if (options?.replace) {
    window.history.replaceState(window.history.state, "", href);
  } else {
    window.history.pushState(window.history.state, "", href);
  }
  window.dispatchEvent(new PopStateEvent("popstate", { state: window.history.state }));
}

/** Destino externo governado — href oficial sob `/apps/` (manifest da
 * plataforma). Qualquer outra URL é recusada. */
export function isGovernedAppsHref(
  href: string | null | undefined,
): href is string {
  return typeof href === "string" && /^\/apps\/[a-z0-9-]+/i.test(href.trim());
}

export function navigateGovernedHref(href: string | null | undefined): void {
  if (!isGovernedAppsHref(href)) return;
  window.location.assign(href);
}
