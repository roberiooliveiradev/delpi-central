/** Catálogo de funcionalidades do Portal Engenharia — apresentação e
 * organização, NUNCA autorização. O acesso efetivo é decidido pela
 * Core/Portal; aqui `requiredPermission` apenas controla se o atalho é
 * exibido (não expor link cuja permissão não foi comprovada pelo host). */

import type { EngineeringView } from "../app/engineeringRoutes";

export type CatalogTarget =
  | { kind: "internal"; view: EngineeringView }
  | { kind: "external"; href: string };

export type CatalogRoute = {
  id: string;
  label: string;
  description?: string;
  target: CatalogTarget;
  /** Permissão Core declarada pelo dono do destino; ausente = sempre
   * visível (destinos internos ou públicos do próprio portal). */
  requiredPermission?: string;
  keywords?: readonly string[];
  /** Destino futuro sem link operacional — renderizado desabilitado. */
  comingSoon?: boolean;
};

export type CatalogSection = {
  id: string;
  title: string;
  description: string;
  routes: readonly CatalogRoute[];
};

export const ENGINEERING_CATALOG: readonly CatalogSection[] = [
  {
    id: "work",
    title: "Trabalho",
    description: "Demandas, solicitações e LMPs do seu dia a dia.",
    routes: [
      {
        id: "my_requests",
        label: "Minhas solicitações",
        description: "Pedidos abertos e acompanhamento",
        target: { kind: "external", href: "/apps/my-requests" },
        requiredPermission: "my-requests.access",
        keywords: ["solicitacoes", "pedidos", "chamados", "requisicoes"],
      },
      {
        id: "lmps",
        label: "LMPs",
        description: "Licitações e medições em acompanhamento",
        target: { kind: "internal", view: "lmps" },
        requiredPermission: "engineering.access",
        keywords: ["lmp", "licitacoes", "medicoes", "dashboard"],
      },
    ],
  },
  {
    id: "insights",
    title: "Análises",
    description: "Visão consolidada e indicadores da Engenharia.",
    routes: [
      {
        id: "overview",
        label: "Visão geral",
        description: "Resumo autorizado da sua área de trabalho",
        target: { kind: "internal", view: "overview" },
        keywords: ["resumo", "indicadores", "visao"],
      },
      {
        id: "dashboard",
        label: "Dashboard Engenharia",
        description: "LMPs no prazo e resultados TRANSFORMA+",
        target: { kind: "external", href: "/apps/dashboard-engineering" },
        requiredPermission: "dashboard-engineering.view",
        keywords: ["dashboard", "indicadores", "transforma", "prazo"],
      },
    ],
  },
  {
    id: "support",
    title: "Suporte",
    description: "Orientação de uso e capacidades futuras.",
    routes: [
      {
        id: "home",
        label: "Início",
        description: "Área de trabalho do Portal Engenharia",
        target: { kind: "internal", view: "home" },
        keywords: ["inicio", "home", "principal"],
      },
      {
        id: "help",
        label: "Ajuda e manual",
        description: "Como usar o Portal Engenharia",
        target: { kind: "internal", view: "help" },
        keywords: ["ajuda", "manual", "suporte", "documentacao"],
      },
      // EVA é especialista de Engenharia (interoperabilidade via MCP
      // quando houver contrato), não aplicativo/rota navegável — sem
      // entrada no catálogo (HOME.R2).
    ],
  },
];

export function findCatalogRoute(routeId: string): CatalogRoute | null {
  for (const section of ENGINEERING_CATALOG) {
    const hit = section.routes.find((route) => route.id === routeId);
    if (hit) return hit;
  }
  return null;
}

export function findCatalogRouteWithSection(
  routeId: string,
): { route: CatalogRoute; section: CatalogSection } | null {
  for (const section of ENGINEERING_CATALOG) {
    const hit = section.routes.find((route) => route.id === routeId);
    if (hit) return { route: hit, section };
  }
  return null;
}

function normalizeText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();
}

function routeAllowed(
  route: CatalogRoute,
  permissions: ReadonlySet<string>,
  isSuperadmin: boolean,
): boolean {
  if (!route.requiredPermission) return true;
  return isSuperadmin || permissions.has(route.requiredPermission);
}

/** Seções visíveis para o usuário — itens sem permissão comprovada não
 * aparecem (o Portal continua sendo a autoridade efetiva). */
export function visibleSections(
  permissions: ReadonlySet<string>,
  isSuperadmin: boolean,
): CatalogSection[] {
  return ENGINEERING_CATALOG.map((section) => ({
    ...section,
    routes: section.routes.filter((route) =>
      routeAllowed(route, permissions, isSuperadmin),
    ),
  })).filter((section) => section.routes.length > 0);
}

function routeMatchesQuery(route: CatalogRoute, query: string): boolean {
  const needle = normalizeText(query);
  if (!needle) return true;
  const haystack = [
    route.label,
    route.description ?? "",
    ...(route.keywords ?? []),
  ]
    .map(normalizeText)
    .join(" ");
  return needle
    .split(/\s+/)
    .every((term) => haystack.includes(term));
}

export function filterSectionsByQuery(
  sections: readonly CatalogSection[],
  query: string,
): CatalogSection[] {
  if (!normalizeText(query)) return [...sections];
  return sections
    .map((section) => ({
      ...section,
      routes: section.routes.filter((route) =>
        routeMatchesQuery(route, query),
      ),
    }))
    .filter((section) => section.routes.length > 0);
}

export type CatalogSearchResult = {
  id: string;
  label: string;
  groupLabel: string;
};

/** Hits de busca (palette + campo do catálogo): nome, descrição e
 * palavras-chave, agrupados pela seção. Nunca retorna item proibido. */
export function searchCatalog(
  query: string,
  sections: readonly CatalogSection[],
): CatalogSearchResult[] {
  const hits: CatalogSearchResult[] = [];
  for (const section of filterSectionsByQuery(sections, query)) {
    for (const route of section.routes) {
      hits.push({
        id: route.id,
        label: route.label,
        groupLabel: section.title,
      });
    }
  }
  return hits;
}

/** Conteúdo textual fixo do portal (copy pt-BR). */
export const HOME_COPY = {
  topbar: {
    ariaLabel: "Navegação do Portal Engenharia",
    searchLabel: "Buscar funcionalidades",
    searchShortcut: "Ctrl+K",
    favoritesTitle: "Favoritos",
    favoritesEmpty: "Nenhum favorito ainda — marque a estrela em um caminho.",
    favoritesOpenAria: "Abrir favoritos",
    favoritesCloseAria: "Fechar favoritos",
    favoritesRemoveLabel: (label: string) => `Remover ${label} dos favoritos`,
    identityFallback: "Usuária(o) da Engenharia",
    collapseLabel: "Recolher menu",
    expandLabel: "Expandir menu",
    menuLabel: "Abrir menu de navegação",
  },
  loading: {
    title: "Preparando sua área de trabalho",
    description: "Consultando tarefas, solicitações e LMPs autorizadas.",
  },
  hero: {
    eyebrow: "Portal Engenharia",
    fallbackGreeting: "Olá!",
    description:
      "Acompanhe suas demandas e continue seu trabalho de Engenharia.",
    scopeBadge: "Minha área de trabalho",
    refreshLabel: "Atualizar",
    refreshingLabel: "Atualizando…",
  },
  events: {
    title: "Eventos e interações",
    subtitle: "Tarefas e solicitações que pedem sua atenção",
    listAriaLabel: "Lista de eventos e interações",
    queueOkTitle: "Tudo em dia — nenhuma pendência no momento.",
    sourcesNotice:
      "Algumas fontes não responderam ou exigem permissão adicional — exibindo apenas o que está autorizado e disponível.",
    openLabel: "Abrir",
    emptyLabel: "Nenhum evento no momento.",
  },
  features: {
    title: "Caminhos e funcionalidades",
    subtitle: "Acessos oficiais da Engenharia na plataforma",
    searchPlaceholder: "Buscar funcionalidade…",
    clearSearch: "Limpar busca",
    searchEmpty: "Nenhuma funcionalidade encontrada.",
    searchAriaLabel: "Buscar no catálogo de funcionalidades",
    recentsTitle: "Últimos acessos",
    gridAriaLabel: "Funcionalidades por categoria",
    pinLabel: "Adicionar aos favoritos",
    unpinLabel: "Remover dos favoritos",
    comingSoonBadge: "Em breve",
    emptyCatalog: "Nenhuma funcionalidade disponível no momento.",
  },
  overview: {
    pageTitle: "Visão geral",
    eyebrow: "Portal Engenharia",
    description:
      "Como está a Engenharia no período selecionado — indicadores oficiais de LMP e TRANSFORMA+.",
    backHome: "Voltar ao Início",
    metricsAriaLabel: "Resumo das fontes disponíveis",
    sourcesTitle: "Fontes da área de trabalho",
    sourcesSubtitle: "Estado de cada informação segundo o owner oficial",
    loadingTitle: "Carregando indicadores de Engenharia",
    loadingDescription:
      "Consultando as fontes oficiais de LMPs e TRANSFORMA+.",
    errorFallback: "Não foi possível carregar a visão geral.",
    generatedAt: (value: string) => `Atualizado em ${value}`,
    refreshLabel: "Atualizar",
    refreshingLabel: "Atualizando…",
    refreshAriaLabel: "Atualizar indicadores da visão geral",
    filtersAriaLabel: "Filtros da visão geral",
    quickPeriodLabel: "Período rápido",
    dateStartLabel: "Data inicial",
    dateEndLabel: "Data final",
    competenceLabel: "Competência",
    branchLabel: "Unidade",
    lmpGroupTitle: "LMP",
    lmpGroupSubtitle: "Prazo, lead time e volume no recorte",
    transformaGroupTitle: "TRANSFORMA+",
    transformaGroupSubtitle: "Ganhos, soluções e retorno no recorte",
    kpiGridAriaLabel: "Indicadores da Engenharia",
    partialNotice:
      "Alguns indicadores não carregaram. Os demais permanecem disponíveis.",
    lmpDeepeningTitle: "LMPs no prazo",
    lmpDeepeningBody:
      "Acompanhe LMPs no Portal Engenharia — indicadores, gráficos, tabela operacional e detalhe por proposta.",
    lmpDeepeningCta: "Abrir acompanhamento de LMPs",
    transformaDeepeningTitle: "TRANSFORMA+",
    transformaDeepeningBody:
      "Abra o Portal TRANSFORMA+ para detalhar soluções, ganhos e retorno.",
    transformaDeepeningCta: "Abrir Portal TRANSFORMA+",
  },
  notFound: {
    title: "Página não encontrada",
    message: "Este endereço não corresponde a uma página do Portal Engenharia.",
    backHome: "Ir para o Início",
  },
};
