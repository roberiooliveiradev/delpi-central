/**
 * Manual in-app dos Painéis TV — conteúdo UI-LOCAL apenas.
 *
 * Autoridade semântica de produto = Product Guide V1 (backend).
 * Aqui ficam somente navegação, rótulos de seção e instruções de tela.
 * NUNCA copiar prosa semântica do Product Guide para este arquivo.
 */

export type UserManualLink = {
  want: string;
  where: string;
  how: string;
  path?: string;
};

export type UserManualSection = {
  id: string;
  /** Rótulo de navegação local (MFE). O título semântico vem do guide. */
  title: string;
  /** Preenchido pelo merge com o Product Guide — nunca via prosa local. */
  intro?: string;
  /** Instruções de interação específicas da tela — nunca semântica de produto. */
  bullets?: readonly string[];
  links?: readonly UserManualLink[];
};

export const USER_MANUAL_CONTENT = {
  backHome: "Voltar ao início",
  scopeNote: "Este manual descreve como usar os Painéis TV no portal.",
  tocTitle: "Neste manual",
  tocAriaLabel: "Sumário do manual",
  sections: [
    {
      id: "overview",
      title: "Visão geral",
      links: [
        {
          want: "Ver minhas programações",
          where: "Início",
          how: "Lista de programações na página inicial",
          path: "/apps/tv-dashboard",
        },
      ],
    },
    {
      id: "playlists",
      title: "Programações",
      links: [
        {
          want: "Criar programação",
          where: "Início",
          how: "Card «Nova programação»",
          path: "/apps/tv-dashboard/playlists/new",
        },
        {
          want: "Compartilhar na TV",
          where: "Editor da programação",
          how: "Ação «link da TV» nos controles da programação",
        },
      ],
    },
    {
      id: "slides",
      title: "Telas",
      links: [
        {
          want: "Adicionar tela",
          where: "Editor",
          how: "Botão «Nova tela» na faixa do editor",
        },
        {
          want: "Navegar entre telas",
          where: "Editor",
          how: "Filmstrip lateral ou setas de navegação",
        },
      ],
    },
    {
      id: "blocks",
      title: "Blocos e elementos",
      links: [
        {
          want: "Inserir elemento",
          where: "Editor",
          how: "Menu «Inserir» na faixa; clique no palco para selecionar e editar",
        },
      ],
    },
    {
      id: "data-sources",
      title: "Fontes de dados",
      links: [
        {
          want: "Adicionar fonte",
          where: "Editor → Dados",
          how: "Catálogo de fontes na aba «Dados» do editor",
        },
        {
          want: "Testar rota",
          where: "Configuração da fonte",
          how: "Botão «Testar rota» mostra a prévia tipada",
        },
      ],
    },
    {
      id: "data-models",
      title: "Modelos de dados",
      links: [
        {
          want: "Preparar dados",
          where: "Editor → Dados",
          how: "«Preparar dados» abre o editor de transformação em modal",
        },
      ],
    },
    {
      id: "bindings",
      title: "Ligações de dados",
      links: [
        {
          want: "Ligar visual aos dados",
          where: "Elemento selecionado",
          how: "Painel de propriedades do elemento mostra as ligações",
        },
      ],
    },
    {
      id: "filters",
      title: "Filtros e camadas",
      links: [
        {
          want: "Filtro da programação",
          where: "Editor",
          how: "Controles da programação → «Filtros padrão»",
        },
        {
          want: "Filtro da fonte",
          where: "Configuração da fonte",
          how: "Campos de parâmetro na configuração da fonte",
        },
      ],
    },
    {
      id: "formats",
      title: "Formatos de exibição",
      links: [
        {
          want: "Formatar número/data",
          where: "Elemento selecionado",
          how: "Opções de formato no painel do elemento",
        },
      ],
    },
    {
      id: "data-discovery",
      title: "Descoberta de rotas",
      links: [
        {
          want: "Encontrar rota de dados",
          where: "Catálogo de fontes",
          how: "Busca por nome ou operationId no catálogo",
        },
      ],
    },
    {
      id: "visual-review",
      title: "Verificação visual",
      links: [
        {
          want: "Pré-visualizar",
          where: "Editor",
          how: "Ação de pré-visualização nos controles da programação",
        },
      ],
    },
  ] satisfies readonly UserManualSection[],
} as const;
