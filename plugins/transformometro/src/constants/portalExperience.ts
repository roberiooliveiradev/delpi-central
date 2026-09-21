import { TRANSFORMOMETRO_ROUTES } from "./routes";
import { describeHttpError } from "../utils/apiErrorMessage";

/** Nome de produto na UI. O bounded context técnico continua Transformômetro. */
export const PORTAL_PRODUCT_NAME = "Portal Transforma+";

export const PORTAL_WELCOME = "Bem-vindo ao Portal Transforma+";

export const PORTAL_HOME_DESCRIPTION =
  "Acompanhe processos, melhorias e resultados da transformação.";

export const PROCESS_LIST_SUBTITLE = "Processos disponíveis no Portal Transforma+.";

export const PORTAL_PAGE_COPY = {
  home: {
    eyebrow: PORTAL_PRODUCT_NAME,
    title: PORTAL_WELCOME,
    description: PORTAL_HOME_DESCRIPTION,
  },
  overview: {
    eyebrow: PORTAL_PRODUCT_NAME,
    title: "Visão geral",
    description: "Indicadores e resultados do programa de transformação.",
  },
  myTasks: {
    eyebrow: "OPERAÇÃO",
    title: "Minhas tarefas",
    description: "Acompanhe e organize ações que exigem sua atenção.",
  },
  processes: {
    eyebrow: "PROCESSOS",
    title: "Meus processos",
    description: PROCESS_LIST_SUBTITLE,
  },
  meetingMinutes: {
    eyebrow: "REGISTROS",
    title: "Atas",
    description: "Reuniões, registros e assinaturas do Transforma+.",
  },
  data: {
    eyebrow: "DADOS",
    title: "Exportar / Importar",
    description: "Backup, transferência e restauração dos dados do Portal Transforma+.",
  },
  administration: {
    eyebrow: PORTAL_PRODUCT_NAME,
    title: "Administração",
    description: "Gerencie configurações e recursos administrativos do Portal Transforma+.",
  },
  settings: {
    eyebrow: PORTAL_PRODUCT_NAME,
    title: "Configurações",
    description: "Gerencie unidades, departamentos e demais cadastros administrativos.",
  },
  help: {
    eyebrow: "Ajuda",
    title: "Manual do usuário",
    description: "Consulte orientações para navegar e utilizar o Portal Transforma+.",
  },
} as const;

export const PROCESS_LIST_EMPTY_MESSAGE =
  "Nenhum processo. Use Novo processo para cadastrar.";

export type PortalPlacement = "topbar" | "launcher" | "utility" | "target";

export type PortalNavStatus = "FUNCTIONAL" | "TO_INVENTORY";

export type PortalCatalogItem = {
  id: string;
  label: string;
  description: string;
  path: string;
  group: string;
  placement: PortalPlacement;
  status: PortalNavStatus;
};

export type DeferredNavItem = {
  id: string;
  label: string;
  placement: PortalPlacement;
  status: "TO_INVENTORY";
  reason: string;
};

/** Áreas principais com destino e owner atuais. Itens sem capability ficam fora. */
export const PORTAL_TOPBAR_ITEMS = [
  { id: "home", label: "Início", path: TRANSFORMOMETRO_ROUTES.home },
  { id: "overview", label: "Visão geral", path: TRANSFORMOMETRO_ROUTES.dashboard },
  { id: "tasks", label: "Minhas tarefas", path: TRANSFORMOMETRO_ROUTES.myTasks },
  { id: "processes", label: "Meus processos", path: TRANSFORMOMETRO_ROUTES.processes },
  { id: "administration", label: "Administração", path: TRANSFORMOMETRO_ROUTES.administration },
  { id: "help", label: "Ajuda", path: TRANSFORMOMETRO_ROUTES.help },
] as const;

/**
 * Sala permanece em outro contexto.
 * Favoritos de rota deste portal são preferência local do MFE, não item da TopBar de negócio.
 */
export const DEFERRED_NAV_ITEMS: readonly DeferredNavItem[] = [
  {
    id: "interaction",
    label: "Sala de interação",
    placement: "topbar",
    status: "TO_INVENTORY",
    reason: "A sala funcional pertence ao commercial-api. Não há contrato transversal no Core.",
  },
  {
    id: "user",
    label: "Usuário",
    placement: "utility",
    status: "TO_INVENTORY",
    reason: "O MFE não recebe display_name sem uma chamada nova.",
  },
];

export const PORTAL_LAUNCHER_GROUPS: readonly {
  id: string;
  title: string;
  description: string;
  links: readonly { id: string; label: string; path: string; description: string }[];
}[] = [
  {
    id: "management",
    title: "Gestão",
    description: "Indicadores e resultados do programa de transformação.",
    links: [
      {
        id: "overview",
        label: "Visão geral",
        path: TRANSFORMOMETRO_ROUTES.dashboard,
        description: "Indicadores e resultados do programa de transformação.",
      },
    ],
  },
  {
    id: "operation",
    title: "Operação",
    description: "Ações que exigem sua atenção.",
    links: [
      {
        id: "my-tasks",
        label: "Minhas tarefas",
        path: TRANSFORMOMETRO_ROUTES.myTasks,
        description: "Crie e acompanhe ações e pendências do Portal.",
      },
    ],
  },
  {
    id: "processes",
    title: "Processos",
    description: "Processos disponíveis no Portal Transforma+.",
    links: [
      {
        id: "processes",
        label: "Meus processos",
        path: TRANSFORMOMETRO_ROUTES.processes,
        description: PROCESS_LIST_SUBTITLE,
      },
    ],
  },
  {
    id: "records",
    title: "Registros",
    description: "Reuniões, registros e backup do portal.",
    links: [
      {
        id: "meeting-minutes",
        label: "Atas",
        path: TRANSFORMOMETRO_ROUTES.meetingMinutes,
        description: "Reuniões, pendências, assinaturas e registros.",
      },
      {
        id: "data",
        label: "Exportar / Importar",
        path: TRANSFORMOMETRO_ROUTES.data,
        description: PORTAL_PAGE_COPY.data.description,
      },
    ],
  },
  {
    id: "administration",
    title: "Administração",
    description: "Configurações administrativas do portal.",
    links: [
      {
        id: "administration",
        label: "Administração",
        path: TRANSFORMOMETRO_ROUTES.administration,
        description: "Configurações administrativas do portal.",
      },
    ],
  },
  {
    id: "help",
    title: "Ajuda",
    description: "Manual do Portal Transforma+.",
    links: [
      {
        id: "user-manual",
        label: "Manual do usuário",
        path: TRANSFORMOMETRO_ROUTES.help,
        description: PORTAL_PAGE_COPY.help.description,
      },
    ],
  },
];

export const PORTAL_ADMIN_LINKS = [
  {
    id: "units",
    label: "Unidades",
    path: TRANSFORMOMETRO_ROUTES.settingsUnits,
    description: "Catálogo de unidades usado nos processos.",
  },
  {
    id: "departments",
    label: "Departamentos",
    path: TRANSFORMOMETRO_ROUTES.settingsDepartments,
    description: "Departamentos vinculados às unidades.",
  },
  {
    id: "resources",
    label: "Recursos compartilhados",
    path: TRANSFORMOMETRO_ROUTES.settingsSharedResources,
    description: "Licenças e ferramentas compartilhadas.",
  },
  {
    id: "data",
    label: "Exportar/Importar",
    path: TRANSFORMOMETRO_ROUTES.data,
    description: "Backup, prévia e confirmação de importação.",
  },
] as const;

/** Busca de funcionalidades do portal. Não indexa processos, atas nem melhorias. */
export const PORTAL_SEARCH_CATALOG: readonly PortalCatalogItem[] = [
  ...PORTAL_TOPBAR_ITEMS.map((item) => ({
    id: item.id,
    label: item.label,
    description: item.label,
    path: item.path,
    group: "Navegação",
    placement: "topbar" as const,
    status: "FUNCTIONAL" as const,
  })),
  ...PORTAL_LAUNCHER_GROUPS.flatMap((group) =>
    group.links.map((link) => ({
      id: link.id,
      label: link.label,
      description: link.description,
      path: link.path,
      group: group.title,
      placement: "launcher" as const,
      status: "FUNCTIONAL" as const,
    })),
  ),
  ...PORTAL_ADMIN_LINKS.filter((link) => link.id !== "data").map((link) => ({
    id: link.id,
    label: link.label,
    description: link.description,
    path: link.path,
    group: "Administração",
    placement: "launcher" as const,
    status: "FUNCTIONAL" as const,
  })),
];

export function filterPortalCatalog(
  query: string,
  options?: { includeAdministration?: boolean },
): PortalCatalogItem[] {
  const needle = query.trim().toLowerCase();
  const includeAdministration = options?.includeAdministration !== false;
  const unique = new Map<string, PortalCatalogItem>();
  for (const item of PORTAL_SEARCH_CATALOG) {
    if (!includeAdministration && (item.group === "Administração" || item.id === "administration")) {
      continue;
    }
    unique.set(item.path, item);
  }
  const items = [...unique.values()];
  if (!needle) return items;
  return items.filter((item) =>
    `${item.label} ${item.group} ${item.description}`.toLowerCase().includes(needle),
  );
}

export function visiblePortalTopBarItems(canManage: boolean) {
  return PORTAL_TOPBAR_ITEMS.filter((item) => canManage || item.id !== "administration");
}

export function visiblePortalLauncherGroups(canManage: boolean) {
  return PORTAL_LAUNCHER_GROUPS.map((group) => ({
    ...group,
    links: group.links.filter((link) => canManage || link.id !== "administration"),
  })).filter((group) => group.links.length > 0);
}

export function isPortalSearchShortcut(event: {
  key: string;
  metaKey: boolean;
  ctrlKey: boolean;
}): boolean {
  return (event.key === "k" || event.key === "K") && (event.metaKey || event.ctrlKey);
}

export function resolvePortalTopBarId(currentPath?: string): string {
  if (!currentPath || currentPath === TRANSFORMOMETRO_ROUTES.home) return "home";
  if (
    currentPath === TRANSFORMOMETRO_ROUTES.help ||
    currentPath.endsWith("/ajuda")
  ) {
    return "help";
  }
  if (
    currentPath === TRANSFORMOMETRO_ROUTES.dashboard ||
    currentPath.endsWith("/dashboard")
  ) {
    return "overview";
  }
  if (currentPath === TRANSFORMOMETRO_ROUTES.myTasks) return "tasks";
  if (currentPath.includes("/processes") || currentPath.includes("/processos")) {
    return "processes";
  }
  if (
    currentPath === TRANSFORMOMETRO_ROUTES.administration ||
    currentPath.includes("/settings") ||
    currentPath.includes("/configuracoes") ||
    currentPath.includes("/cadastros") ||
    currentPath.includes("/filiais") ||
    currentPath.includes("/setores") ||
    currentPath.includes("/recursos")
  ) {
    return "administration";
  }
  return "";
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
