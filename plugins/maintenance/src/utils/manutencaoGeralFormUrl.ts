import manifest from "../../maintenance.manifest.json";
import { MAINTENANCE_ROUTES } from "../constants/routes";

const MANUTENCAO_GERAL_PATHS = new Set<string>([
  MAINTENANCE_ROUTES.manutencaoGeral("01"),
  MAINTENANCE_ROUTES.manutencaoGeralLegacy,
]);

function isExternalHttpUrl(value: string | undefined): value is string {
  if (!value) return false;
  return /^https?:\/\//i.test(value.trim());
}

function entryFromManifest(): string | undefined {
  for (const route of manifest.routes) {
    if (!MANUTENCAO_GERAL_PATHS.has(route.path)) continue;
    const entry = typeof route.entry === "string" ? route.entry.trim() : "";
    if (isExternalHttpUrl(entry)) return entry;
  }
  return undefined;
}

/** URL do formulário — portal repassa `routes[].entry` via `alternateEntry`; fallback lê o manifesto local. */
export function resolveManutencaoGeralFormUrl(alternateEntry?: string): string | undefined {
  const fromHost = alternateEntry?.trim();
  if (isExternalHttpUrl(fromHost)) return fromHost;
  return entryFromManifest();
}
