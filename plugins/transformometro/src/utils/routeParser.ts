import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";
import type { RecursoWorkspaceSectionId } from "../ui/configuracoes/configuracoesWorkspaceNav";
import { defaultRecursoSection } from "../ui/configuracoes/configuracoesWorkspaceNav";

export type TransformometroView =
  | "dashboard"
  | "dados"
  | "configuracoes"
  | "filiais"
  | "filial"
  | "setores"
  | "setor"
  | "recursos"
  | "recurso"
  | "processos"
  | "processo"
  | "instancia"
  | "revisao";

export type ParsedTransformometroRoute = {
  view: TransformometroView;
  processoId?: string;
  instanciaId?: string;
  revisaoId?: string;
  filialId?: string;
  setorId?: string;
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

function matchConfiguracoesRecurso(path: string) {
  return path.match(
    /^\/apps\/transformometro\/(?:configuracoes|cadastros)\/recursos\/([^/]+)$/
  );
}

function matchConfiguracoesSetor(path: string) {
  return path.match(
    /^\/apps\/transformometro\/(?:configuracoes|cadastros)\/departamentos\/([^/]+)$/
  );
}

function matchConfiguracoesFilial(path: string) {
  return path.match(/^\/apps\/transformometro\/(?:configuracoes|cadastros)\/unidades\/([^/]+)$/);
}

export function parseTransformometroPath(pathname: string): ParsedTransformometroRoute {
  const path = normalizeTransformometroPath(pathname);

  const canonicalRevisaoMatch = path.match(
    /^\/apps\/transformometro\/processos\/([^/]+)\/instancias\/([^/]+)\/revisoes\/([^/]+)$/
  );
  if (canonicalRevisaoMatch) {
    return {
      view: "revisao",
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
      view: "revisao",
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
      view: "instancia",
      processoId: instanciaMatch[1],
      instanciaId: instanciaMatch[2],
    };
  }

  const processoMatch = path.match(/^\/apps\/transformometro\/processos\/([^/]+)$/);
  if (processoMatch) {
    return { view: "processo", processoId: processoMatch[1] };
  }

  const configuracoesRecursoMatch = matchConfiguracoesRecurso(path);
  if (configuracoesRecursoMatch) {
    return { view: "recurso", recursoId: configuracoesRecursoMatch[1] };
  }

  const configuracoesSetorMatch = matchConfiguracoesSetor(path);
  if (configuracoesSetorMatch) {
    return { view: "setor", setorId: configuracoesSetorMatch[1] };
  }

  const configuracoesFilialMatch = matchConfiguracoesFilial(path);
  if (configuracoesFilialMatch) {
    return { view: "filial", filialId: configuracoesFilialMatch[1] };
  }

  const legacyRecursoMatch = path.match(/^\/apps\/transformometro\/recursos\/([^/]+)$/);
  if (legacyRecursoMatch) {
    return { view: "recurso", recursoId: legacyRecursoMatch[1] };
  }

  const legacyFilialMatch = path.match(/^\/apps\/transformometro\/filiais\/([^/]+)$/);
  if (legacyFilialMatch) {
    return { view: "filial", filialId: legacyFilialMatch[1] };
  }

  const legacySetorMatch = path.match(/^\/apps\/transformometro\/setores\/([^/]+)$/);
  if (legacySetorMatch) {
    return { view: "setor", setorId: legacySetorMatch[1] };
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

  if (
    path === TRANSFORMOMETRO_ROUTES.configuracoesDepartamentos ||
    path.endsWith("/configuracoes/departamentos") ||
    path.endsWith("/cadastros/departamentos") ||
    path === TRANSFORMOMETRO_ROUTES.setores ||
    path.endsWith("/setores")
  ) {
    return { view: "configuracoes" };
  }

  if (
    path === TRANSFORMOMETRO_ROUTES.configuracoesRecursos ||
    path.endsWith("/configuracoes/recursos") ||
    path.endsWith("/cadastros/recursos") ||
    path === TRANSFORMOMETRO_ROUTES.recursos ||
    path.endsWith("/recursos")
  ) {
    return { view: "configuracoes" };
  }

  if (
    path === TRANSFORMOMETRO_ROUTES.configuracoesUnidades ||
    path.endsWith("/configuracoes/unidades") ||
    path.endsWith("/cadastros/unidades") ||
    path === TRANSFORMOMETRO_ROUTES.filiais ||
    path.endsWith("/filiais") ||
    path === TRANSFORMOMETRO_ROUTES.configuracoes ||
    path.endsWith("/configuracoes") ||
    path.endsWith("/cadastros")
  ) {
    return { view: "configuracoes" };
  }

  if (path === TRANSFORMOMETRO_ROUTES.processos || path.endsWith("/processos")) {
    return { view: "processos" };
  }

  return { view: "dashboard" };
}

export function isConfiguracoesWorkspaceRoute(route: ParsedTransformometroRoute): boolean {
  return (
    route.view === "configuracoes" ||
    route.view === "filial" ||
    route.view === "setor" ||
    route.view === "recurso"
  );
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
  return `${TRANSFORMOMETRO_ROUTES.configuracoesRecursos}/${recursoId}`;
}

export function buildRecursoSectionPath(
  recursoId: string,
  section: RecursoWorkspaceSectionId
): string {
  const base = buildRecursoPath(recursoId);
  if (section === defaultRecursoSection()) return base;
  return `${base}#${section}`;
}

export function buildFilialPath(filialId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.configuracoesUnidades}/${filialId}`;
}

export function buildSetorPath(setorId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.configuracoesDepartamentos}/${setorId}`;
}
