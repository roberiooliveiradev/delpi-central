/**
 * Catálogo canônico do hub Início: seção (1º) → rotas (2º).
 * Paths só via viewId + buildPluginPath — sem URL absoluta.
 *
 * IMP-MFE-HOME: somente rotas implementadas em runtime podem entrar
 * aqui. Rotas futuras (Central de Fechamento, Visão geral etc.) NÃO
 * são indexadas até existirem.
 */
import type { PluginNavigationTarget } from "../app/pluginRoutes";

export type HubCapability = "manage" | "always";

export type HubRouteKind = "navigate" | "create";

export type HubRouteDef = {
  id: string;
  label: string;
  viewId: PluginNavigationTarget;
  search?: string;
  requiredCap: HubCapability;
  keywords?: readonly string[];
  kind?: HubRouteKind;
};

export type HubSectionId = "portal" | "closing";

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
    id: "portal",
    title: "Portal",
    description: "Áreas do Portal Controladoria & Finanças.",
    iconKey: "portal",
    routes: [
      {
        id: "home",
        label: "Início",
        viewId: "home",
        requiredCap: "always",
        keywords: [
          "inicio",
          "início",
          "home",
          "portal",
          "começo",
          "comeco",
          "saudação",
          "saudacao",
        ],
      },
    ],
  },
  {
    id: "closing",
    title: "Central de Fechamento",
    description: "Consultas e acompanhamento do fechamento mensal.",
    iconKey: "closing",
    routes: [
      {
        id: "closing-checklist",
        label: "Checklist da competência",
        viewId: "checklist",
        requiredCap: "always",
        keywords: [
          "checklist",
          "competencia",
          "competência",
          "fechamento",
          "itens",
          "esperados",
          "mensal",
          "entregaveis",
          "entregáveis",
        ],
      },
      {
        id: "financial-settlements",
        label: "Baixas financeiras",
        viewId: "financial_settlements",
        requiredCap: "always",
        keywords: [
          "baixas",
          "pagamentos",
          "recebimentos",
          "pagar",
          "receber",
          "financeiro",
          "settlement",
          "fechamento",
          "liquidacao",
          "liquidação",
        ],
      },
      {
        id: "closing-admin",
        label: "Administração do checklist",
        viewId: "checklist_admin",
        requiredCap: "manage",
        keywords: [
          "administracao",
          "administração",
          "template",
          "checklist",
          "versao",
          "versão",
          "publicar",
          "mestre",
          "configuracao",
          "configuração",
        ],
      },
      {
        id: "pendencies",
        label: "Pendências do fechamento",
        viewId: "pendencies",
        requiredCap: "always",
        keywords: [
          "pendencias",
          "pendências",
          "classificacao",
          "classificação",
          "triagem",
          "analise",
          "análise",
          "divergencia",
          "divergência",
          "fila",
          "fechamento",
        ],
      },
      {
        id: "closing-packages",
        label: "Pacotes e revisão",
        viewId: "packages",
        requiredCap: "always",
        keywords: [
          "pacotes",
          "destinatario",
          "destinatário",
          "revisao",
          "revisão",
          "envio",
          "aceite",
          "esclarecimento",
          "contabil",
          "contábil",
          "fiscal",
          "fechamento",
        ],
      },
      {
        id: "closing-cockpit",
        label: "Cockpit do fechamento",
        viewId: "cockpit",
        requiredCap: "always",
        keywords: [
          "cockpit",
          "visao",
          "visão",
          "geral",
          "situacao",
          "situação",
          "status",
          "conclusao",
          "conclusão",
          "fechamento",
        ],
      },
      {
        id: "stock-inventory",
        label: "Estoque histórico — P7",
        viewId: "stock_inventory",
        requiredCap: "always",
        keywords: [
          "estoque",
          "inventario",
          "inventário",
          "p7",
          "matr460",
          "saldos",
          "armazem",
          "armazém",
          "produtos",
          "fechamento",
          "historico",
          "histórico",
        ],
      },
    ],
  },
] as const;

export const HUB_CONTENT = {
  productName: "Portal Controladoria & Finanças",
  features: {
    title: "Caminhos e funcionalidades",
    subtitle: "Busque ou abra uma área do portal.",
    gridAriaLabel: "Caminhos do Portal Controladoria & Finanças",
    empty: "Nenhuma funcionalidade disponível para o seu acesso.",
    searchPlaceholder: "Buscar caminhos e funcionalidades…",
    searchAriaLabel: "Buscar caminhos e funcionalidades",
    searchEmpty: "Nenhum caminho encontrado",
    clearSearch: "Limpar busca",
    recentsTitle: "Últimos acessos",
  },
  events: {
    title: "Eventos e interações",
    subtitle: "Tarefas e alertas do seu dia.",
    listAriaLabel: "Eventos e interações pendentes",
    unavailable: "Eventos operacionais indisponíveis nesta versão.",
  },
  palette: {
    title: "Buscar no Portal Controladoria & Finanças",
    placeholder: "Ir para caminho ou funcionalidade…",
    empty: "Nenhum resultado",
    closeAriaLabel: "Fechar busca",
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

/** Pesos do ranking da busca de caminhos (label > keywords > description > title > viewId). */
const SEARCH_FIELD_WEIGHTS = {
  label: 100,
  keywords: 80,
  description: 50,
  title: 40,
  viewId: 20,
} as const;

const SEARCH_PREFIX_BOOST = 10;

function normalizeSearchText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .trim();
}

/** Tokens da query; ignora partículas de 1 caractere (ex.: «à» → «a»). */
export function tokenizeQuery(query: string): string[] {
  const normalized = normalizeSearchText(query);
  if (!normalized) return [];
  return normalized.split(/[^a-z0-9]+/u).filter((token) => token.length >= 2);
}

type RouteSearchField = {
  weight: number;
  text: string;
};

function buildRouteSearchIndex(
  section: HubSectionDef,
  route: HubRouteDef,
): RouteSearchField[] {
  return [
    { weight: SEARCH_FIELD_WEIGHTS.label, text: normalizeSearchText(route.label) },
    {
      weight: SEARCH_FIELD_WEIGHTS.keywords,
      text: normalizeSearchText((route.keywords ?? []).join(" ")),
    },
    {
      weight: SEARCH_FIELD_WEIGHTS.description,
      text: normalizeSearchText(section.description ?? ""),
    },
    { weight: SEARCH_FIELD_WEIGHTS.title, text: normalizeSearchText(section.title) },
    { weight: SEARCH_FIELD_WEIGHTS.viewId, text: normalizeSearchText(route.viewId) },
  ].filter((field) => field.text.length > 0);
}

function tokenFieldScore(field: RouteSearchField, token: string): number {
  if (!field.text.includes(token)) return 0;
  const words = field.text.split(/[^a-z0-9]+/u).filter(Boolean);
  const isPrefix = words.some((word) => word.startsWith(token));
  return field.weight + (isPrefix ? SEARCH_PREFIX_BOOST : 0);
}

/**
 * Score de relevância da rota para a query.
 * 0 = sem match. Todos os tokens (≥2 chars) precisam casar em algum campo (AND).
 */
export function scoreRouteMatch(
  section: HubSectionDef,
  route: HubRouteDef,
  query: string,
): number {
  const tokens = tokenizeQuery(query);
  if (tokens.length === 0) return 0;
  const fields = buildRouteSearchIndex(section, route);
  let total = 0;
  for (const token of tokens) {
    let best = 0;
    for (const field of fields) {
      best = Math.max(best, tokenFieldScore(field, token));
    }
    if (best === 0) return 0;
    total += best;
  }
  return total;
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
      routes: section.routes.filter(
        (route) => scoreRouteMatch(section, route, q) > 0,
      ),
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
  const ranked: Array<{ hit: HubSearchHit; score: number; order: number }> = [];
  let order = 0;
  for (const section of sections) {
    for (const route of section.routes) {
      const score = scoreRouteMatch(section, route, q);
      if (score <= 0) continue;
      ranked.push({
        hit: {
          id: route.id,
          label: route.label,
          groupLabel: section.title,
          viewId: route.viewId,
          search: route.search,
        },
        score,
        order: order++,
      });
    }
  }
  ranked.sort((a, b) => b.score - a.score || a.order - b.order);
  return ranked.slice(0, limit).map((entry) => entry.hit);
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
