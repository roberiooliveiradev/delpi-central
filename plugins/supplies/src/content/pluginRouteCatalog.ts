import type { PluginRoutableView } from "../app/pluginRoutes";

export type HubCapability =
  | "always"
  | "analytics"
  | "purchaseRequests"
  | "operations"
  | "administration";

export type HubRouteDef = {
  id: string;
  label: string;
  viewId: PluginRoutableView;
  requiredCap: HubCapability;
  keywords?: readonly string[];
};

export type HubSectionDef = {
  id: string;
  title: string;
  description?: string;
  routes: readonly HubRouteDef[];
};

export type HubCapabilities = Record<Exclude<HubCapability, "always">, boolean>;

export const HUB_SECTIONS: readonly HubSectionDef[] = [
  {
    id: "attention",
    title: "Início",
    description: "Ação e descoberta no Portal.",
    routes: [
      {
        id: "home",
        label: "Início",
        viewId: "home",
        requiredCap: "always",
        keywords: ["inicio", "home", "atencao"],
      },
      {
        id: "my_tasks",
        label: "Minhas tarefas",
        viewId: "my_tasks",
        requiredCap: "always",
        keywords: ["tarefas", "fila"],
      },
    ],
  },
  {
    id: "analytics",
    title: "Análises",
    description: "Overview e indicadores.",
    routes: [
      {
        id: "overview",
        label: "Visão geral",
        viewId: "overview",
        requiredCap: "analytics",
        keywords: ["overview", "kpi", "visao"],
      },
      {
        id: "negotiations",
        label: "Negociações",
        viewId: "negotiations",
        requiredCap: "analytics",
        keywords: ["negociacao", "otd"],
      },
      {
        id: "indicators",
        label: "Indicadores",
        viewId: "indicators",
        requiredCap: "analytics",
        keywords: ["indicadores", "idd"],
      },
    ],
  },
  {
    id: "purchase_requests",
    title: "Solicitações de Compras",
    routes: [
      {
        id: "purchase_requests",
        label: "Solicitações",
        viewId: "purchase_requests",
        requiredCap: "purchaseRequests",
        keywords: ["sc", "solicitacao", "compras"],
      },
    ],
  },
  {
    id: "operations",
    title: "Operações",
    description: "Pedidos, entregas, itens e estoques.",
    routes: [
      {
        id: "purchase_orders",
        label: "Pedidos de compra",
        viewId: "purchase_orders",
        requiredCap: "operations",
        keywords: ["pc", "pedido"],
      },
      {
        id: "deliveries",
        label: "Entregas",
        viewId: "deliveries",
        requiredCap: "operations",
        keywords: ["entrega", "sd1"],
      },
      {
        id: "suppliers",
        label: "Fornecedores",
        viewId: "suppliers",
        requiredCap: "operations",
        keywords: ["fornecedor"],
      },
      {
        id: "products",
        label: "Produtos",
        viewId: "products",
        requiredCap: "operations",
        keywords: ["produto", "item"],
      },
      {
        id: "inventory",
        label: "Estoque",
        viewId: "inventory",
        requiredCap: "operations",
        keywords: ["estoque"],
      },
      {
        id: "safety_stock",
        label: "Estoque de segurança",
        viewId: "safety_stock",
        requiredCap: "operations",
        keywords: ["estseg", "seguranca"],
      },
    ],
  },
  {
    id: "administration",
    title: "Administração",
    routes: [
      {
        id: "administration",
        label: "Administração",
        viewId: "administration",
        requiredCap: "administration",
        keywords: ["admin", "mapeamento"],
      },
    ],
  },
  {
    id: "help",
    title: "Ajuda",
    routes: [
      {
        id: "help",
        label: "Ajuda",
        viewId: "help",
        requiredCap: "always",
        keywords: ["manual", "faq", "ajuda"],
      },
    ],
  },
];

export const HUB_CONTENT = {
  productName: "Portal Suprimentos",
  home: {
    eyebrow: "Portal Suprimentos",
    title: "Início",
    description:
      "Ação e descoberta no seu escopo. Indicadores do período ficam na Visão geral.",
    helpAriaLabel: "Ajuda: Início vs Visão geral",
    attentionTitle: "Atenção",
    attentionSubtitle: "Atalhos autorizados para o que precisa de ação agora.",
    attentionEmpty: "Nenhum atalho de atenção disponível para o seu acesso.",
    attentionError: "Não foi possível carregar a atenção. Os caminhos abaixo continuam disponíveis.",
    attentionLoading: "Carregando atenção…",
    attentionRefresh: "Atualizar",
    attentionQueueOk: "Atenção em dia — nenhum atalho pendente no momento.",
    attentionOpenPaths: "Ver caminhos",
    pathsTitle: "Caminhos e funcionalidades",
    pathsSubtitle: "Abra as áreas liberadas para você.",
    pathsEmpty: "Nenhuma funcionalidade disponível para o seu acesso.",
    pathsGridAriaLabel: "Seções do Portal Suprimentos",
    searchLabel: "Buscar caminhos",
    searchPlaceholder: "Buscar caminhos e funcionalidades…",
    searchAriaLabel: "Buscar caminhos do Portal",
    searchEmpty: "Nenhum caminho encontrado",
    searchHelpAriaLabel: "Ajuda: busca do Início",
    clearSearch: "Limpar busca",
    recentsTitle: "Últimos acessos",
    recentsHelpAriaLabel: "Ajuda: últimos acessos",
    favoritesTitle: "Favoritos",
    favoritesHelpAriaLabel: "Ajuda: favoritos",
    favoritesEmpty: "Nenhum favorito ainda. Use a estrela nos caminhos.",
    favoritesMenuOpenAriaLabel: "Abrir favoritos",
    favoritesMenuCloseAriaLabel: "Fechar favoritos",
    queueOkHelpAriaLabel: "Ajuda: atenção em dia",
    pinLabel: "Favoritar",
    unpinLabel: "Remover dos favoritos",
    onboardingTitle: "Comece por aqui",
  },
  palette: {
    title: "Ir para",
    placeholder: "Buscar área do Portal Suprimentos",
    empty: "Nenhuma área encontrada",
    closeAriaLabel: "Fechar busca",
  },
} as const;

/** Ordem de atalhos do onboarding (máx. 3 na UI). */
const ONBOARDING_ROUTE_IDS = [
  "purchase_requests",
  "overview",
  "safety_stock",
  "my_tasks",
  "help",
] as const;

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

/** Seções do grid do Início — omitem o atalho «Início» (já estamos nele). */
export function resolveHomePathSections(
  capabilities: HubCapabilities,
  sections: readonly HubSectionDef[] = HUB_SECTIONS,
): HubSectionDef[] {
  return resolveHubSections(capabilities, sections)
    .map((section) => ({
      ...section,
      routes: section.routes.filter((route) => route.id !== "home"),
    }))
    .filter((section) => section.routes.length > 0);
}

export function pickOnboardingShortcuts(
  capabilities: HubCapabilities,
  limit = 3,
): HubRouteDef[] {
  const sections = resolveHomePathSections(capabilities);
  const byId = new Map<string, HubRouteDef>();
  for (const section of sections) {
    for (const route of section.routes) {
      byId.set(route.id, route);
    }
  }
  const picked: HubRouteDef[] = [];
  for (const id of ONBOARDING_ROUTE_IDS) {
    const route = byId.get(id);
    if (route) picked.push(route);
    if (picked.length >= limit) break;
  }
  return picked;
}

export function findHubRouteById(
  sections: readonly HubSectionDef[],
  routeId: string,
): HubRouteDef | undefined {
  for (const section of sections) {
    const match = section.routes.find((route) => route.id === routeId);
    if (match) return match;
  }
  return undefined;
}

export function hubRouteLabelByView(viewId: string): string | undefined {
  for (const section of HUB_SECTIONS) {
    const match = section.routes.find((route) => route.viewId === viewId);
    if (match) return match.label;
  }
  return undefined;
}

function normalizeSearchText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .trim();
}

export type HubSearchHit = {
  id: string;
  label: string;
  groupLabel: string;
};

export function collectSearchHits(
  sections: readonly HubSectionDef[],
  query: string,
  limit = 8,
): HubSearchHit[] {
  const needle = normalizeSearchText(query);
  const hits: HubSearchHit[] = [];
  for (const section of sections) {
    for (const route of section.routes) {
      const haystack = normalizeSearchText(
        [route.label, section.title, ...(route.keywords ?? [])].join(" "),
      );
      if (!needle || haystack.includes(needle)) {
        hits.push({ id: route.id, label: route.label, groupLabel: section.title });
      }
      if (hits.length >= limit) return hits;
    }
  }
  return hits;
}
