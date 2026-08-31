import manifest from "../../maintenance.manifest.json";
import { MAINTENANCE_ROUTES } from "../constants/routes";

const MANUTENCAO_GERAL_PATHS = new Set<string>([
  MAINTENANCE_ROUTES.manutencaoGeral("01"),
  MAINTENANCE_ROUTES.manutencaoGeralLegacy,
]);

/** Rotas do manifesto vivo (`/me/apps` → AppHost → `appRoutes`). */
export type HostAppRoute = {
  path: string;
  entry?: string | null;
  openInNewTab?: boolean | null;
};

type ManifestRoute = {
  path?: string;
  entry?: string | null;
  openInNewTab?: boolean | null;
};

function localManifestRoutes(): ManifestRoute[] {
  return Array.isArray(manifest.routes) ? (manifest.routes as ManifestRoute[]) : [];
}

export function isExternalHttpUrl(value: string | undefined | null): value is string {
  if (!value) return false;
  return /^https?:\/\//i.test(value.trim());
}

function findRouteInList(
  routes: Array<{ path?: string; entry?: string | null; openInNewTab?: boolean | null }>,
  path: string,
): { path?: string; entry?: string | null; openInNewTab?: boolean | null } | undefined {
  const normalized = path.trim();
  return routes.find((route) => route.path === normalized);
}

/** Catálogo efetivo: manifesto do portal tem prioridade; JSON local só fallback (dev/standalone). */
function resolveRouteCatalog(hostRoutes?: HostAppRoute[] | null): ManifestRoute[] {
  if (hostRoutes && hostRoutes.length > 0) {
    return hostRoutes;
  }
  return localManifestRoutes();
}

function entryFromManutencaoGeralRoutes(routes: ManifestRoute[]): string | undefined {
  for (const route of routes) {
    if (!route.path || !MANUTENCAO_GERAL_PATHS.has(route.path)) continue;
    const entry = typeof route.entry === "string" ? route.entry.trim() : "";
    if (isExternalHttpUrl(entry)) return entry;
  }
  return undefined;
}

export type ResolveManutencaoGeralFormUrlOptions = {
  alternateEntry?: string;
  hostRoutes?: HostAppRoute[] | null;
};

/**
 * URL do formulário Manutenção geral.
 * Ordem: `alternateEntry` da rota atual → Entry no manifesto vivo (`hostRoutes`) → JSON local.
 */
export function resolveManutencaoGeralFormUrl(
  alternateEntryOrOptions?: string | ResolveManutencaoGeralFormUrlOptions,
): string | undefined {
  const options: ResolveManutencaoGeralFormUrlOptions =
    typeof alternateEntryOrOptions === "string" || alternateEntryOrOptions == null
      ? { alternateEntry: alternateEntryOrOptions ?? undefined }
      : alternateEntryOrOptions;

  const fromHost = options.alternateEntry?.trim();
  if (isExternalHttpUrl(fromHost)) return fromHost;

  return entryFromManutencaoGeralRoutes(resolveRouteCatalog(options.hostRoutes));
}

/**
 * Resolve se a rota deve abrir em nova aba e qual URL usar
 * (Entry http(s) do manifesto vivo ou path absoluto no portal).
 */
export function resolveManifestRouteOpenTarget(
  path: string,
  options?: {
    alternateEntry?: string;
    origin?: string;
    hostRoutes?: HostAppRoute[] | null;
  },
): { openInNewTab: boolean; url: string } | null {
  const route = findRouteInList(resolveRouteCatalog(options?.hostRoutes), path);
  if (!route?.openInNewTab) {
    return null;
  }

  const entry =
    (isExternalHttpUrl(options?.alternateEntry) ? options?.alternateEntry.trim() : "") ||
    (typeof route.entry === "string" ? route.entry.trim() : "");

  if (isExternalHttpUrl(entry)) {
    return { openInNewTab: true, url: entry };
  }

  const origin =
    options?.origin ??
    (typeof window !== "undefined" ? window.location.origin : "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const base = String(origin || "").replace(/\/$/, "");
  return {
    openInNewTab: true,
    url: base ? `${base}${normalizedPath}` : normalizedPath,
  };
}

/** Abre a rota em nova aba quando `openInNewTab` estiver no manifesto. Retorna true se abriu. */
export function tryOpenManifestPathInNewTab(
  path: string,
  options?: {
    alternateEntry?: string;
    origin?: string;
    hostRoutes?: HostAppRoute[] | null;
  },
): boolean {
  const target = resolveManifestRouteOpenTarget(path, options);
  if (!target) return false;
  window.open(target.url, "_blank", "noopener,noreferrer");
  return true;
}

export function shouldOpenManutencaoGeralInNewTab(
  hostRoutes?: HostAppRoute[] | null,
): boolean {
  return resolveRouteCatalog(hostRoutes).some(
    (route) =>
      Boolean(route.path) &&
      MANUTENCAO_GERAL_PATHS.has(route.path!) &&
      Boolean(route.openInNewTab),
  );
}
