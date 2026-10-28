/**
 * Catálogo canônico do hub Início: seção (1º) → rotas (2º).
 * Paths só via viewId + buildPluginPath — sem URL absoluta.
 *
 * Somente rotas implementadas em runtime podem entrar aqui. Rotas
 * futuras (Visão geral dedicada, Sala de interação, Ajuda) NÃO são
 * indexadas até existirem. «Minhas tarefas» existe em runtime, mas
 * está fora da navegação desta release por decisão de escopo
 * (CF-PROC0072-CLARA-COMPLETE-001 §18) — rota e código preservados.
 */
import type { PluginNavigationTarget } from "../app/pluginRoutes";

export type HubCapability = "access" | "manage" | "accessDre";

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

export type HubSectionId = "portal" | "closing" | "closing_dre";

export type HubSectionDef = {
  id: HubSectionId;
  title: string;
  description?: string;
  iconKey: HubSectionId;
  routes: readonly HubRouteDef[];
};

export type HubCapabilities = Record<HubCapability, boolean>;

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
        requiredCap: "access",
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
      {
        id: "profile",
        label: "Meu perfil",
        viewId: "profile",
        requiredCap: "access",
        keywords: [
          "perfil",
          "usuario",
          "usuário",
          "identidade",
          "foto",
          "grupos",
          "permissoes",
          "permissões",
          "vinculos",
          "vínculos",
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
        id: "monthly-closing",
        label: "Fechamento mensal",
        viewId: "monthly_closing",
        requiredCap: "access",
        keywords: [
          "fechamento",
          "mensal",
          "competencia",
          "competência",
          "checklist",
          "cockpit",
          "pendencias",
          "pendências",
          "pacotes",
          "estoque",
          "baixas",
          "visao",
          "visão",
          "geral",
          "situacao",
          "situação",
          "status",
          "conclusao",
          "conclusão",
        ],
      },
      {
        id: "monthly-closing-documents",
        label: "Documentos e interações",
        viewId: "monthly_closing",
        search: "tab=documents",
        requiredCap: "access",
        keywords: [
          "documentos",
          "interacoes",
          "interações",
          "evidencias",
          "evidências",
          "anexos",
          "upload",
          "checklist",
          "entregaveis",
          "entregáveis",
          "fechamento",
        ],
      },
      {
        id: "monthly-closing-reports",
        label: "Relatórios e divergências",
        viewId: "monthly_closing",
        search: "tab=reports",
        requiredCap: "access",
        keywords: [
          "relatorios",
          "relatórios",
          "divergencias",
          "divergências",
          "r01",
          "r02",
          "r03",
          "r15",
          "baixas",
          "estoque",
          "totvs",
          "conciliacao",
          "conciliação",
          "fechamento",
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
        id: "documents-admin",
        label: "Documentos do fechamento",
        viewId: "documents_admin",
        requiredCap: "manage",
        keywords: [
          "documentos",
          "documento",
          "catalogo",
          "catálogo",
          "cadastro",
          "exigencia",
          "exigência",
          "vigencia",
          "vigência",
          "contabilidade",
          "dre",
          "obrigatorio",
          "obrigatório",
          "configuracao",
          "configuração",
        ],
      },
      {
        id: "catalogs-admin",
        label: "Catálogos governados",
        viewId: "catalogs_admin",
        requiredCap: "manage",
        keywords: [
          "catalogos",
          "catálogos",
          "bancos",
          "contas",
          "motivos",
          "rejeicao",
          "rejeição",
          "anexos",
          "elegibilidade",
          "areas",
          "áreas",
          "obrigatorias",
          "obrigatórias",
          "configuracao",
          "configuração",
        ],
      },
    ],
  },
  // RW04 — seção do público externo DRE no catálogo ÚNICO: mesma Home,
  // mesma estrutura de cards; a audiência é resolvida por capability
  // (`access.dre`), nunca por composição paralela. Funcionalidades DRE
  // futuras entram aqui sob `accessDre` — sem novas permissions por
  // página.
  {
    id: "closing_dre",
    title: "Central de Fechamento",
    description:
      "Consulte os documentos disponibilizados pela Controladoria e acompanhe as interações relacionadas ao fechamento.",
    iconKey: "closing",
    routes: [
      {
        id: "dre-monthly-closing",
        label: "Fechamento Mensal",
        viewId: "received_documents",
        requiredCap: "accessDre",
        keywords: [
          "fechamento",
          "mensal",
          "documentos",
          "recebidos",
          "interacoes",
          "interações",
          "entrega",
          "competencia",
          "competência",
          "dre",
          "contabilidade",
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
        (route) => capabilities[route.requiredCap],
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
