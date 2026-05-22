import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";

export type TransformometroView =
  | "home"
  | "dashboard"
  | "import"
  | "recursos"
  | "processos"
  | "processo";

export type ParsedTransformometroRoute = {
  view: TransformometroView;
  processoId?: string;
  revisaoId?: string;
};

export function normalizeTransformometroPath(pathname: string): string {
  if (!pathname) return TRANSFORMOMETRO_ROUTES.home;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parseTransformometroPath(pathname: string): ParsedTransformometroRoute {
  const path = normalizeTransformometroPath(pathname);

  const revisaoMatch = path.match(
    /^\/apps\/transformometro\/processos\/([^/]+)\/revisoes\/([^/]+)$/
  );
  if (revisaoMatch) {
    return {
      view: "processo",
      processoId: revisaoMatch[1],
      revisaoId: revisaoMatch[2],
    };
  }

  const processoMatch = path.match(/^\/apps\/transformometro\/processos\/([^/]+)$/);
  if (processoMatch) {
    return { view: "processo", processoId: processoMatch[1] };
  }

  if (path === TRANSFORMOMETRO_ROUTES.dashboard || path.endsWith("/dashboard")) {
    return { view: "dashboard" };
  }

  if (path === TRANSFORMOMETRO_ROUTES.import || path.endsWith("/import")) {
    return { view: "import" };
  }

  if (path === TRANSFORMOMETRO_ROUTES.recursos || path.endsWith("/recursos")) {
    return { view: "recursos" };
  }

  if (path === TRANSFORMOMETRO_ROUTES.processos || path.endsWith("/processos")) {
    return { view: "processos" };
  }

  return { view: "home" };
}

export function buildProcessoPath(processoId: string, revisaoId?: string | null): string {
  const base = `${TRANSFORMOMETRO_ROUTES.processos}/${processoId}`;
  if (revisaoId) {
    return `${base}/revisoes/${revisaoId}`;
  }
  return base;
}
