import { TRANSFORMOMETRO_ROUTES } from "./routes";
import { describeHttpError } from "../utils/apiErrorMessage";
import { TM_HELP_TOOLTIPS } from "../content/helpTooltips";

/** Nome de produto na UI. O bounded context técnico continua Transformômetro. */
export const PORTAL_PRODUCT_NAME = "Portal Transforma+";

export const PORTAL_WELCOME = "Bem-vindo ao Portal Transforma+";

export const PORTAL_HOME_SUBTITLE = "Escolha um caminho. Indicadores ficam na Visão geral.";

export const PROCESS_LIST_SUBTITLE = TM_HELP_TOOLTIPS.processos.listaEscopo;

export const PROCESS_LIST_EMPTY_MESSAGE =
  "Nenhum processo. Use Novo processo para cadastrar.";

export type PortalNavLink = {
  path: string;
  label: string;
  description: string;
};

export const PORTAL_NAV_LINKS: readonly PortalNavLink[] = [
  {
    path: TRANSFORMOMETRO_ROUTES.home,
    label: "Início",
    description: "Orientação e atalhos do portal.",
  },
  {
    path: TRANSFORMOMETRO_ROUTES.dashboard,
    label: "Visão geral",
    description: "Gestão à vista dos indicadores já calculados.",
  },
  {
    path: TRANSFORMOMETRO_ROUTES.processes,
    label: "Meus processos",
    description: "Processos disponíveis no seu escopo de acesso.",
  },
  {
    path: TRANSFORMOMETRO_ROUTES.meetingMinutes,
    label: "Atas",
    description: "Lista, pendências e assinaturas.",
  },
  {
    path: TRANSFORMOMETRO_ROUTES.settingsUnits,
    label: "Configurações",
    description: "Unidades, departamentos e recursos.",
  },
  {
    path: TRANSFORMOMETRO_ROUTES.data,
    label: "Exportar/Importar",
    description: "Backup, prévia e confirmação de importação.",
  },
];

export const PORTAL_HOME_LINKS = PORTAL_NAV_LINKS.filter((link) => link.path !== TRANSFORMOMETRO_ROUTES.home);

export function isPortalNavActive(path: string, currentPath?: string): boolean {
  if (!currentPath) {
    return path === TRANSFORMOMETRO_ROUTES.home;
  }
  if (path === TRANSFORMOMETRO_ROUTES.home) {
    return currentPath === path;
  }
  if (path === TRANSFORMOMETRO_ROUTES.dashboard) {
    return currentPath === path || currentPath.endsWith("/dashboard");
  }
  if (path === TRANSFORMOMETRO_ROUTES.processes) {
    return currentPath === path || currentPath.startsWith(`${path}/`);
  }
  if (path === TRANSFORMOMETRO_ROUTES.settingsUnits) {
    return (
      currentPath.includes("/settings") ||
      currentPath.includes("/configuracoes") ||
      currentPath.includes("/cadastros") ||
      currentPath.includes("/filiais") ||
      currentPath.includes("/setores") ||
      currentPath.includes("/recursos")
    );
  }
  if (path === TRANSFORMOMETRO_ROUTES.meetingMinutes) {
    return (
      currentPath === path ||
      currentPath.startsWith(`${path}/`) ||
      currentPath.includes("/meeting-minutes") ||
      currentPath.includes("/atas") ||
      currentPath.includes("/my-signature") ||
      currentPath.includes("/minha-assinatura")
    );
  }
  return currentPath === path || currentPath.startsWith(`${path}/`);
}

export function buildProcessListQuery(
  searchQ: string,
  status: string,
): { q?: string; status?: string } {
  const params: { q?: string; status?: string } = {};
  if (status) params.status = status;
  if (searchQ.trim()) params.q = searchQ.trim();
  return params;
}

export function processListPlaceholder(httpStatus: number | null, error: string | null): string {
  if (httpStatus === 403) {
    return error?.trim() || describeHttpError(403);
  }
  if (error) return error;
  return PROCESS_LIST_EMPTY_MESSAGE;
}
