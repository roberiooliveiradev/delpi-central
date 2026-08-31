import manifest from "../../maintenance.manifest.json";
import { MAINTENANCE_ROUTES } from "../constants/routes";

const MANUTENCAO_GERAL_PATHS = new Set<string>([
  MAINTENANCE_ROUTES.manutencaoGeral("01"),
  MAINTENANCE_ROUTES.manutencaoGeralLegacy,
]);

type ManifestRoute = {
  path?: string;
  entry?: string | null;
  openInNewTab?: boolean | null;
};

function manifestRoutes(): ManifestRoute[] {
  return Array.isArray(manifest.routes) ? (manifest.routes as ManifestRoute[]) : [];
}

export function isExternalHttpUrl(value: string | undefined | null): value is string {
  if (!value) return false;
  return /^https?:\/\//i.test(value.trim());
}

function findManifestRoute(path: string): ManifestRoute | undefined {
  const normalized = path.trim();
  return manifestRoutes().find((route) => route.path === normalized);
}

function entryFromManutencaoGeralManifest(): string | undefined {
  for (const route of manifestRoutes()) {
    if (!route.path || !MANUTENCAO_GERAL_PATHS.has(route.path)) continue;
    const entry = typeof route.entry === "string" ? route.entry.trim() : "";
    if (isExternalHttpUrl(entry)) return entry;
  }
  return undefined;
}

/** URL do formulário — portal repassa `routes[].entry` via `alternateEntry`; fallback lê o manifesto local. */
export function resolveManutencaoGeralFormUrl(alternateEntry?: string): string | undefined {
  const fromHost = alternateEntry?.trim();
  if (isExternalHttpUrl(fromHost)) return fromHost;
  return entryFromManutencaoGeralManifest();
}

/**
 * Resolve se uma rota do manifesto local deve abrir em nova aba e qual URL usar
 * (Entry http(s) ou path absoluto no portal).
 */
export function resolveManifestRouteOpenTarget(
  path: string,
  options?: { alternateEntry?: string; origin?: string },
): { openInNewTab: boolean; url: string } | null {
  const route = findManifestRoute(path);
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
  options?: { alternateEntry?: string; origin?: string },
): boolean {
  const target = resolveManifestRouteOpenTarget(path, options);
  if (!target) return false;
  window.open(target.url, "_blank", "noopener,noreferrer");
  return true;
}

export function shouldOpenManutencaoGeralInNewTab(): boolean {
  return manifestRoutes().some(
    (route) =>
      Boolean(route.path) &&
      MANUTENCAO_GERAL_PATHS.has(route.path!) &&
      Boolean(route.openInNewTab),
  );
}
