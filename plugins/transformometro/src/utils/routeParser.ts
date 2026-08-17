import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";
import type { RecursoWorkspaceSectionId } from "../ui/settings/settingsWorkspaceNav";
import { defaultRecursoSection } from "../ui/settings/settingsWorkspaceNav";

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
  | "processoDiagramaEdit"
  | "instancia"
  | "instanciaDiagramaEdit"
  | "revisao"
  | "revisaoDiagramaEdit"
  | "atas"
  | "ata"
  | "ataEdit"
  | "ataNew"
  | "ataSign"
  | "atasPending"
  | "minhaAssinatura";

export type ParsedTransformometroRoute = {
  view: TransformometroView;
  processoId?: string;
  instanciaId?: string;
  revisaoId?: string;
  filialId?: string;
  setorId?: string;
  recursoId?: string;
  ataId?: string;
  legacyRevisaoPath?: boolean;
};

export function normalizeTransformometroPath(pathname: string): string {
  if (!pathname) return TRANSFORMOMETRO_ROUTES.home;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

/** Reescreve bookmarks/links PT para o path canônico EN. */
export function canonicalizeTransformometroPath(pathname: string): string {
  let path = normalizeTransformometroPath(pathname);
  if (!path.startsWith("/apps/transformometro")) return path;

  path = path.replace(
    /^\/apps\/transformometro\/minha-assinatura$/,
    TRANSFORMOMETRO_ROUTES.mySignature,
  );
  path = path.replace(/^\/apps\/transformometro\/dados$/, TRANSFORMOMETRO_ROUTES.data);
  path = path.replace(/^\/apps\/transformometro\/atas(?=\/|$)/, "/apps/transformometro/meeting-minutes");
  path = path.replace(/^\/apps\/transformometro\/processos(?=\/|$)/, "/apps/transformometro/processes");
  path = path.replace(/^\/apps\/transformometro\/configuracoes(?=\/|$)/, "/apps/transformometro/settings");
  path = path.replace(/^\/apps\/transformometro\/cadastros(?=\/|$)/, "/apps/transformometro/settings");
  path = path.replace(/^\/apps\/transformometro\/filiais(?=\/|$)/, "/apps/transformometro/settings/units");
  path = path.replace(/^\/apps\/transformometro\/setores(?=\/|$)/, "/apps/transformometro/settings/departments");
  path = path.replace(/^\/apps\/transformometro\/recursos(?=\/|$)/, "/apps/transformometro/settings/shared-resources");

  path = path.replace(/\/settings\/unidades(?=\/|$)/, "/settings/units");
  path = path.replace(/\/settings\/departamentos(?=\/|$)/, "/settings/departments");
  path = path.replace(/\/settings\/recursos(?=\/|$)/, "/settings/shared-resources");
  path = path.replace(/\/instancias(?=\/|$)/g, "/instances");
  path = path.replace(/\/revisoes(?=\/|$)/g, "/revisions");
  path = path.replace(/\/diagrama(?=\/|$)/g, "/diagram");

  return path;
}

function matchSettingsSharedResource(path: string) {
  return path.match(
    /^\/apps\/transformometro\/(?:settings|configuracoes|cadastros)\/(?:shared-resources|recursos)\/([^/]+)$/,
  );
}

function matchSettingsDepartment(path: string) {
  return path.match(
    /^\/apps\/transformometro\/(?:settings|configuracoes|cadastros)\/(?:departments|departamentos)\/([^/]+)$/,
  );
}

function matchSettingsUnit(path: string) {
  return path.match(
    /^\/apps\/transformometro\/(?:settings|configuracoes|cadastros)\/(?:units|unidades)\/([^/]+)$/,
  );
}

export function parseTransformometroPath(pathname: string): ParsedTransformometroRoute {
  const path = canonicalizeTransformometroPath(pathname);

  if (path === TRANSFORMOMETRO_ROUTES.meetingMinutes) return { view: "atas" };
  if (path === `${TRANSFORMOMETRO_ROUTES.meetingMinutes}/new`) return { view: "ataNew" };
  if (path === TRANSFORMOMETRO_ROUTES.meetingMinutesPending) return { view: "atasPending" };
  if (path === TRANSFORMOMETRO_ROUTES.mySignature) return { view: "minhaAssinatura" };

  const ataMatch = path.match(
    /^\/apps\/transformometro\/(?:meeting-minutes|atas)\/([^/]+)(?:\/(edit|sign))?$/,
  );
  if (ataMatch) {
    return {
      view: ataMatch[2] === "edit" ? "ataEdit" : ataMatch[2] === "sign" ? "ataSign" : "ata",
      ataId: ataMatch[1],
    };
  }

  const revisaoDiagramaEditMatch = path.match(
    /^\/apps\/transformometro\/(?:processes|processos)\/([^/]+)\/(?:instances|instancias)\/([^/]+)\/(?:revisions|revisoes)\/([^/]+)\/(?:diagram|diagrama)\/edit$/,
  );
  if (revisaoDiagramaEditMatch) {
    return {
      view: "revisaoDiagramaEdit",
      processoId: revisaoDiagramaEditMatch[1],
      instanciaId: revisaoDiagramaEditMatch[2],
      revisaoId: revisaoDiagramaEditMatch[3],
    };
  }

  const instanciaDiagramaEditMatch = path.match(
    /^\/apps\/transformometro\/(?:processes|processos)\/([^/]+)\/(?:instances|instancias)\/([^/]+)\/(?:diagram|diagrama)\/edit$/,
  );
  if (instanciaDiagramaEditMatch) {
    return {
      view: "instanciaDiagramaEdit",
      processoId: instanciaDiagramaEditMatch[1],
      instanciaId: instanciaDiagramaEditMatch[2],
    };
  }

  const processoDiagramaEditMatch = path.match(
    /^\/apps\/transformometro\/(?:processes|processos)\/([^/]+)\/(?:diagram|diagrama)\/edit$/,
  );
  if (processoDiagramaEditMatch) {
    return {
      view: "processoDiagramaEdit",
      processoId: processoDiagramaEditMatch[1],
    };
  }

  const canonicalRevisaoMatch = path.match(
    /^\/apps\/transformometro\/(?:processes|processos)\/([^/]+)\/(?:instances|instancias)\/([^/]+)\/(?:revisions|revisoes)\/([^/]+)$/,
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
    /^\/apps\/transformometro\/(?:processes|processos)\/([^/]+)\/(?:revisions|revisoes)\/([^/]+)$/,
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
    /^\/apps\/transformometro\/(?:processes|processos)\/([^/]+)\/(?:instances|instancias)\/([^/]+)$/,
  );
  if (instanciaMatch) {
    return {
      view: "instancia",
      processoId: instanciaMatch[1],
      instanciaId: instanciaMatch[2],
    };
  }

  const processoMatch = path.match(/^\/apps\/transformometro\/(?:processes|processos)\/([^/]+)$/);
  if (processoMatch) {
    return { view: "processo", processoId: processoMatch[1] };
  }

  const configuracoesRecursoMatch = matchSettingsSharedResource(path);
  if (configuracoesRecursoMatch) {
    return { view: "recurso", recursoId: configuracoesRecursoMatch[1] };
  }

  const configuracoesSetorMatch = matchSettingsDepartment(path);
  if (configuracoesSetorMatch) {
    return { view: "setor", setorId: configuracoesSetorMatch[1] };
  }

  const configuracoesFilialMatch = matchSettingsUnit(path);
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

  if (path === TRANSFORMOMETRO_ROUTES.data || path.endsWith("/data") || path.endsWith("/dados")) {
    return { view: "dados" };
  }

  if (
    path === TRANSFORMOMETRO_ROUTES.settingsDepartments ||
    path.endsWith("/settings/departments") ||
    path.endsWith("/configuracoes/departamentos") ||
    path.endsWith("/cadastros/departamentos") ||
    path === TRANSFORMOMETRO_ROUTES.setores ||
    path.endsWith("/setores")
  ) {
    return { view: "configuracoes" };
  }

  if (
    path === TRANSFORMOMETRO_ROUTES.settingsSharedResources ||
    path.endsWith("/settings/shared-resources") ||
    path.endsWith("/configuracoes/recursos") ||
    path.endsWith("/cadastros/recursos") ||
    path === TRANSFORMOMETRO_ROUTES.recursos ||
    path.endsWith("/recursos")
  ) {
    return { view: "configuracoes" };
  }

  if (
    path === TRANSFORMOMETRO_ROUTES.settingsUnits ||
    path.endsWith("/settings/units") ||
    path.endsWith("/configuracoes/unidades") ||
    path.endsWith("/cadastros/unidades") ||
    path === TRANSFORMOMETRO_ROUTES.filiais ||
    path.endsWith("/filiais") ||
    path === TRANSFORMOMETRO_ROUTES.settings ||
    path.endsWith("/settings") ||
    path.endsWith("/configuracoes") ||
    path.endsWith("/cadastros")
  ) {
    return { view: "configuracoes" };
  }

  if (
    path === TRANSFORMOMETRO_ROUTES.processes ||
    path.endsWith("/processes") ||
    path.endsWith("/processos")
  ) {
    return { view: "processos" };
  }

  return { view: "dashboard" };
}

export function isSettingsWorkspaceRoute(route: ParsedTransformometroRoute): boolean {
  return (
    route.view === "configuracoes" ||
    route.view === "filial" ||
    route.view === "setor" ||
    route.view === "recurso"
  );
}

export function buildInstanciaPath(processoId: string, instanciaId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.processes}/${processoId}/instances/${instanciaId}`;
}

export function buildProcessoPath(
  processoId: string,
  revisaoId?: string | null,
  instanciaId?: string | null,
): string {
  if (revisaoId && instanciaId) {
    return `${buildInstanciaPath(processoId, instanciaId)}/revisions/${revisaoId}`;
  }
  if (instanciaId) {
    return buildInstanciaPath(processoId, instanciaId);
  }
  return `${TRANSFORMOMETRO_ROUTES.processes}/${processoId}`;
}

export function buildProcessoDiagramaEditPath(processoId: string): string {
  return `${buildProcessoPath(processoId)}/diagram/edit`;
}

export function buildInstanciaDiagramaEditPath(processoId: string, instanciaId: string): string {
  return `${buildInstanciaPath(processoId, instanciaId)}/diagram/edit`;
}

export function buildRevisaoDiagramaEditPath(
  processoId: string,
  instanciaId: string,
  revisaoId: string,
): string {
  return `${buildProcessoPath(processoId, revisaoId, instanciaId)}/diagram/edit`;
}

export function buildRecursoPath(recursoId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.settingsSharedResources}/${recursoId}`;
}

export function buildRecursoSectionPath(
  recursoId: string,
  section: RecursoWorkspaceSectionId,
): string {
  const base = buildRecursoPath(recursoId);
  if (section === defaultRecursoSection()) return base;
  return `${base}#${section}`;
}

export function buildFilialPath(filialId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.settingsUnits}/${filialId}`;
}

export function buildSetorPath(setorId: string): string {
  return `${TRANSFORMOMETRO_ROUTES.settingsDepartments}/${setorId}`;
}
