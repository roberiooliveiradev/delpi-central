/**
 * Catálogo canônico do hub Início: seção (1º) → rotas (2º).
 * Paths só via viewId + buildPluginPath — sem URL absoluta.
 */
import type { PluginNavigationTarget } from "../app/pluginRoutes";

export type HubCapability =
  | "analytics"
  | "worklist"
  | "proposals"
  | "customers"
  | "admin"
  | "always";

export type HubRouteKind = "navigate" | "create";

export type HubRouteDef = {
  id: string;
  label: string;
  viewId: PluginNavigationTarget;
  search?: string;
  requiredCap: HubCapability;
  keywords?: readonly string[];
  kind?: HubRouteKind;
  /** Badge source key resolved by HomePage. */
  badgeKey?: "tasks_overdue" | "tasks_today" | "orders_late";
};

export type HubSectionId =
  | "operations"
  | "management"
  | "documents"
  | "help"
  | "administration";

export type HubSectionDef = {
  id: HubSectionId;
  title: string;
  description?: string;
  iconKey: HubSectionId;
  routes: readonly HubRouteDef[];
};

export type HubCapabilities = Record<Exclude<HubCapability, "always">, boolean>;

export const HUB_SECTIONS: readonly HubSectionDef[] = [
  {
    id: "operations",
    title: "Operação",
    description: "Fila do dia, pedidos e carteira.",
    iconKey: "operations",
    routes: [
      {
        id: "my_tasks",
        label: "Minhas tarefas",
        viewId: "my_tasks",
        requiredCap: "worklist",
        keywords: ["tarefas", "follow-up", "followups", "fila"],
      },
      {
        id: "tasks_overdue",
        label: "Atrasadas",
        viewId: "my_tasks",
        search: "?bucket=overdue",
        requiredCap: "worklist",
        keywords: ["atraso", "atrasadas", "overdue"],
        badgeKey: "tasks_overdue",
      },
      {
        id: "tasks_today",
        label: "Hoje",
        viewId: "my_tasks",
        search: "?bucket=today",
        requiredCap: "worklist",
        keywords: ["hoje", "today"],
        badgeKey: "tasks_today",
      },
      {
        id: "create_task",
        label: "Nova tarefa",
        viewId: "my_tasks",
        search: "?createTask=1",
        requiredCap: "worklist",
        kind: "create",
        keywords: ["nova", "criar", "follow-up", "tarefa"],
      },
      {
        id: "open_orders",
        label: "Meus pedidos",
        viewId: "open_orders",
        requiredCap: "always",
        keywords: ["pedidos", "ov", "venda", "aberto"],
      },
      {
        id: "orders_late",
        label: "Em atraso",
        viewId: "open_orders",
        search: "?focus=late",
        requiredCap: "always",
        keywords: ["atraso", "atrasados", "late"],
        badgeKey: "orders_late",
      },
      {
        id: "orders_billable",
        label: "Pode faturar",
        viewId: "open_orders",
        search: "?stock=com_estoque",
        requiredCap: "always",
        keywords: ["faturar", "estoque", "billable", "faturamento"],
      },
      {
        id: "orders_postponed",
        label: "Postergado",
        viewId: "open_orders",
        search: "?postponed=1",
        requiredCap: "always",
        keywords: ["postergado", "futuro", "disponivel"],
      },
      {
        id: "orders_ready_board",
        label: "Pronto para faturar (board)",
        viewId: "open_orders",
        search: "?view=board&stage=ready_to_invoice",
        requiredCap: "always",
        keywords: ["kanban", "pronto", "faturar", "board"],
      },
      {
        id: "customers",
        label: "Minha Carteira",
        viewId: "customers",
        requiredCap: "customers",
        keywords: ["carteira", "clientes", "conta"],
      },
      {
        id: "interaction_rooms",
        label: "Sala de interação",
        viewId: "interaction_rooms",
        requiredCap: "always",
        keywords: [
          "sala",
          "interacao",
          "interação",
          "conversa",
          "menção",
          "mencao",
          "chat",
          "inbox",
        ],
      },
    ],
  },
  {
    id: "management",
    title: "Gestão à vista",
    description: "Indicadores e drills do período.",
    iconKey: "management",
    routes: [
      {
        id: "overview",
        label: "Visão geral",
        viewId: "overview",
        requiredCap: "analytics",
        keywords: ["overview", "kpi", "rol", "gestão", "gestao"],
      },
      {
        id: "analytics_otd",
        label: "Pontualidade (OTD)",
        viewId: "analytics_otd",
        requiredCap: "analytics",
        keywords: ["otd", "pontualidade", "entrega", "prazo"],
      },
      {
        id: "analytics_opportunities",
        label: "Oportunidades",
        viewId: "analytics_opportunities",
        requiredCap: "analytics",
        keywords: ["oportunidades", "ov", "funil", "ciclo"],
      },
    ],
  },
  {
    id: "documents",
    title: "Documentos",
    description: "Propostas comerciais e PDF.",
    iconKey: "documents",
    routes: [
      {
        id: "proposals",
        label: "Propostas comerciais",
        viewId: "proposals",
        requiredCap: "proposals",
        keywords: ["propostas", "proposta", "ady", "pdf", "documento"],
      },
    ],
  },
  {
    id: "help",
    title: "Ajuda",
    description: "Manual e dúvidas frequentes.",
    iconKey: "help",
    routes: [
      {
        id: "user_manual",
        label: "Manual do usuário",
        viewId: "help",
        requiredCap: "always",
        keywords: [
          "manual",
          "ajuda",
          "help",
          "duvida",
          "dúvida",
          "faq",
          "como usar",
          "onde ir",
        ],
      },
    ],
  },
  {
    id: "administration",
    title: "Administração",
    description: "Carteiras, membros e transferências.",
    iconKey: "administration",
    routes: [
      {
        id: "administration",
        label: "Painel",
        viewId: "administration",
        requiredCap: "admin",
        keywords: ["admin", "painel", "administração", "administracao"],
      },
      {
        id: "administration_portfolios",
        label: "Carteiras",
        viewId: "administration_portfolios",
        requiredCap: "admin",
        keywords: ["carteiras", "seller", "portfolios"],
      },
      {
        id: "administration_team",
        label: "Equipe",
        viewId: "administration_team",
        requiredCap: "admin",
        keywords: ["membros", "equipe", "team", "online"],
      },
      {
        id: "administration_groups",
        label: "Grupos",
        viewId: "administration_groups",
        requiredCap: "admin",
        keywords: ["grupos", "groups", "vendedores", "auxiliares"],
      },
    ],
  },
] as const;

export const HUB_CONTENT = {
  productName: "Portal Comercial",
  features: {
    title: "Caminhos e funcionalidades",
    subtitle: "Busque ou abra uma aplicação do portal.",
    gridAriaLabel: "Caminhos do Portal Comercial",
    empty: "Nenhuma funcionalidade disponível para o seu acesso.",
    searchPlaceholder: "Buscar caminhos e funcionalidades…",
    searchAriaLabel: "Buscar caminhos e funcionalidades",
    searchEmpty: "Nenhum caminho encontrado",
    clearSearch: "Limpar busca",
    recentsTitle: "Últimos acessos",
    favoritesTitle: "Favoritos",
    favoritesEmpty: "Nenhum favorito ainda. Use a estrela nos caminhos do Início.",
    favoritesMenuOpenAriaLabel: "Abrir favoritos",
    favoritesMenuCloseAriaLabel: "Fechar favoritos",
    pinLabel: "Adicionar aos favoritos",
    unpinLabel: "Remover dos favoritos",
    favoritesLoadError: "Não foi possível carregar favoritos.",
    favoritesSaveError: "Não foi possível salvar favoritos.",
  },
  events: {
    title: "Eventos e interações",
    subtitle: "Tarefas e alertas do seu dia.",
    cta: "Abrir Minhas tarefas",
    refresh: "Atualizar",
    loading: "Carregando eventos…",
    queueLabel: "Fila",
    listAriaLabel: "Eventos e interações pendentes",
    openTask: "Abrir",
    openOverdue: "Ver atrasadas",
    noDueDate: "Sem prazo",
    queueOkTitle: "Fila em dia",
    queueOkCta: "Abrir Minhas tarefas",
    buckets: {
      overdue: "Atrasadas",
      today: "Hoje",
      later: "Depois",
    },
  },
  palette: {
    title: "Buscar no Portal Comercial",
    placeholder: "Ir para caminho ou funcionalidade…",
    empty: "Nenhum resultado",
    closeAriaLabel: "Fechar busca",
  },
  heroCta: {
    ordersLate: (n: number) =>
      n === 1
        ? "Você tem 1 pedido em atraso"
        : `Você tem ${n.toLocaleString("pt-BR")} pedidos em atraso`,
    tasksOverdue: (n: number) =>
      n === 1
        ? "Você tem 1 tarefa atrasada"
        : `Você tem ${n.toLocaleString("pt-BR")} tarefas atrasadas`,
    tasksToday: (n: number) =>
      n === 1
        ? "Você tem 1 tarefa para hoje"
        : `Você tem ${n.toLocaleString("pt-BR")} tarefas para hoje`,
  },
} as const;

/** Label canônico do app (2º nível) para PagePath / recentes. */
export function hubRouteLabelByView(
  viewId: PluginNavigationTarget,
  search?: string,
): string | undefined {
  const normalized = search?.startsWith("?") ? search : search ? `?${search}` : undefined;
  for (const section of HUB_SECTIONS) {
    for (const route of section.routes) {
      if (route.viewId !== viewId) continue;
      const routeSearch = route.search;
      if ((routeSearch ?? undefined) === (normalized ?? undefined)) {
        return route.label;
      }
    }
  }
  for (const section of HUB_SECTIONS) {
    for (const route of section.routes) {
      if (route.viewId === viewId && !route.search && route.kind !== "create") {
        return route.label;
      }
    }
  }
  return undefined;
}

export function resolveHubSections(
  capabilities: HubCapabilities,
  sections: readonly HubSectionDef[] = HUB_SECTIONS,
): HubSectionDef[] {
  return sections
    .map((section) => ({
      ...section,
      routes: section.routes.filter(
        (route) => route.requiredCap === "always" || capabilities[route.requiredCap],
      ),
    }))
    .filter((section) => section.routes.length > 0);
}

function normalizeSearchText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .trim();
}

function routeMatches(route: HubRouteDef, sectionTitle: string, query: string): boolean {
  if (!query) return true;
  const haystack = [
    sectionTitle,
    route.label,
    ...(route.keywords ?? []),
    route.viewId,
  ]
    .map(normalizeSearchText)
    .join(" ");
  return haystack.includes(query);
}

export function filterRouteCatalog(
  sections: readonly HubSectionDef[],
  query: string,
): HubSectionDef[] {
  const q = normalizeSearchText(query);
  if (!q) return [...sections];
  return sections
    .map((section) => ({
      ...section,
      routes: section.routes.filter((route) => routeMatches(route, section.title, q)),
    }))
    .filter((section) => section.routes.length > 0);
}

export type HubSearchHit = {
  id: string;
  label: string;
  groupLabel: string;
  viewId: PluginNavigationTarget;
  search?: string;
};

export function collectSearchHits(
  sections: readonly HubSectionDef[],
  query: string,
  limit = 8,
): HubSearchHit[] {
  const q = normalizeSearchText(query);
  if (!q) return [];
  const hits: HubSearchHit[] = [];
  for (const section of sections) {
    for (const route of section.routes) {
      if (!routeMatches(route, section.title, q)) continue;
      hits.push({
        id: route.id,
        label: route.label,
        groupLabel: section.title,
        viewId: route.viewId,
        search: route.search,
      });
      if (hits.length >= limit) return hits;
    }
  }
  return hits;
}

export function findHubRouteById(
  sections: readonly HubSectionDef[],
  routeId: string,
): HubRouteDef | undefined {
  for (const section of sections) {
    const found = section.routes.find((route) => route.id === routeId);
    if (found) return found;
  }
  return undefined;
}

export type HomeContextualCta = {
  id: "orders_late" | "tasks_overdue" | "tasks_today";
  label: string;
  viewId: PluginNavigationTarget;
  search?: string;
};

export function resolveHomeContextualCta(input: {
  ordersLate: number | null;
  tasksOverdue: number | null;
  tasksToday: number | null;
  ready: boolean;
}): HomeContextualCta | null {
  if (!input.ready) return null;
  if (input.ordersLate != null && input.ordersLate > 0) {
    return {
      id: "orders_late",
      label: HUB_CONTENT.heroCta.ordersLate(input.ordersLate),
      viewId: "open_orders",
      search: "?focus=late",
    };
  }
  if (input.tasksOverdue != null && input.tasksOverdue > 0) {
    return {
      id: "tasks_overdue",
      label: HUB_CONTENT.heroCta.tasksOverdue(input.tasksOverdue),
      viewId: "my_tasks",
      search: "?bucket=overdue",
    };
  }
  if (input.tasksToday != null && input.tasksToday > 0) {
    return {
      id: "tasks_today",
      label: HUB_CONTENT.heroCta.tasksToday(input.tasksToday),
      viewId: "my_tasks",
      search: "?bucket=today",
    };
  }
  return null;
}
