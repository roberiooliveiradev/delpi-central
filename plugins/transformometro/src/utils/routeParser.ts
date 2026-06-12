import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";

export type TransformometroView =
  | "dashboard"
  | "dados"
  | "filiais"
  | "setores"
  | "recursos"
  | "recurso"
  | "processos"
  | "processo";

export type ParsedTransformometroRoute = {
  view: TransformometroView;
  processoId?: string;
  instanciaId?: string;
  revisaoId?: string;
  recursoId?: string;
  legacyRevisaoPath?: boolean;
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

  const canonicalRevisaoMatch = path.match(
    /^\/apps\/transformometro\/processos\/([^/]+)\/instancias\/([^/]+)\/revisoes\/([^/]+)$/
  );
  if (canonicalRevisaoMatch) {
    return {
      view: "processo",
      processoId: canonicalRevisaoMatch[1],
      instanciaId: canonicalRevisaoMatch[2],
      revisaoId: canonicalRevisaoMatch[3],
    };
  }

  const legacyRevisaoMatch = path.match(
    /^\/apps\/transformometro\/processos\/([^/]+)\/revisoes\/([^/]+)$/
  );
  if (legacyRevisaoMatch) {
    return {
      view: "processo",
      processoId: legacyRevisaoMatch[1],
      revisaoId: legacyRevisaoMatch[2],
      legacyRevisaoPath: true,
    };
  }

  const instanciaMatch = path.match(
    /^\/apps\/transformometro\/processos\/([^/]+)\/instancias\/([^/]+)$/
  );
  if (instanciaMatch) {
    return {
      view: "processo",
      processoId: instanciaMatch[1],
      instanciaId: instanciaMatch[2],
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

  if (path === TRANSFORMOMETRO_ROUTES.filiais || path.endsWith("/filiais")) {
    return { view: "filiais" };
  }

  if (path === TRANSFORMOMETRO_ROUTES.recursos || path.endsWith("/recursos")) {
    return { view: "recursos" };
  }

  if (path === TRANSFORMOMETRO_ROUTES.processos || path.endsWith("/processos")) {
    return { view: "processos" };
  }

  return { view: "dashboard" };
}

export function buildInstanciaPath(processoId: string, instanciaId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.processos}/${processoId}/instancias/${instanciaId}`;
}

export function buildProcessoPath(
  processoId: string,
  revisaoId?: string | null,
  instanciaId?: string | null
): string {
  if (revisaoId && instanciaId) {
    return `${buildInstanciaPath(processoId, instanciaId)}/revisoes/${revisaoId}`;
  }
  if (instanciaId) {
    return buildInstanciaPath(processoId, instanciaId);
  }
  return `${TRANSFORMOMETRO_ROUTES.processos}/${processoId}`;
}

export function buildRecursoPath(recursoId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.recursos}/${recursoId}`;
}
