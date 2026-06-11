import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";

export type TransformometroView =
  | "dashboard"
  | "dados"
  | "setores"
  | "recursos"
  | "recurso"
  | "processos"
  | "processo";

export type ParsedTransformometroRoute = {
  view: TransformometroView;
  processoId?: string;
  revisaoId?: string;
  recursoId?: string;
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

  const recursoMatch = path.match(/^\/apps\/transformometro\/recursos\/([^/]+)$/);
  if (recursoMatch) {
    return { view: "recurso", recursoId: recursoMatch[1] };
  }

  if (
    path === TRANSFORMOMETRO_ROUTES.home ||
    path === TRANSFORMOMETRO_ROUTES.dashboard ||
    path.endsWith("/dashboard")
  ) {
    return { view: "dashboard" };
  }

  if (path === TRANSFORMOMETRO_ROUTES.dados || path.endsWith("/dados")) {
    return { view: "dados" };
  }

  if (path === TRANSFORMOMETRO_ROUTES.setores || path.endsWith("/setores")) {
    return { view: "setores" };
  }

  if (path === TRANSFORMOMETRO_ROUTES.recursos || path.endsWith("/recursos")) {
    return { view: "recursos" };
  }

  if (path === TRANSFORMOMETRO_ROUTES.processos || path.endsWith("/processos")) {
    return { view: "processos" };
  }

  return { view: "dashboard" };
}

export function buildProcessoPath(processoId: string, revisaoId?: string | null): string {
  const base = `${TRANSFORMOMETRO_ROUTES.processos}/${processoId}`;
  if (revisaoId) {
    return `${base}/revisoes/${revisaoId}`;
  }
  return base;
}

export function buildRecursoPath(recursoId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.recursos}/${recursoId}`;
}
