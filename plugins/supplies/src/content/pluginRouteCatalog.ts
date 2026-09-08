import type { PluginNavigationTarget } from "../app/pluginRoutes";

export type HubCapability =
  | "always"
  | "analytics"
  | "purchaseRequests"
  | "operations"
  | "administration";

export type HubRouteDef = {
  id: string;
  label: string;
  viewId: PluginNavigationTarget;
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
  palette: {
    title: "Ir para",
    placeholder: "Buscar área do Portal Suprimentos",
    empty: "Nenhuma área encontrada",
    closeAriaLabel: "Fechar busca",
  },
} as const;

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
