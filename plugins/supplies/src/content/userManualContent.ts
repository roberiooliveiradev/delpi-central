import { GLOSSARY_CONTENT } from "./glossaryContent";

/**
 * Conteúdo PT-BR do Manual do usuário (página /help) — Portal Suprimentos E4.
 * Espelho markdown completo fica para E16.
 */
export type UserManualLinkRow = {
  want: string;
  where: string;
  how: string;
};

export type UserManualFaq = {
  q: string;
  a: string;
};

export type UserManualSection = {
  id: string;
  title: string;
  intro?: string;
  bullets?: readonly string[];
  links?: readonly UserManualLinkRow[];
  faqs?: readonly UserManualFaq[];
  glossary?: readonly { term: string; meaning: string }[];
};

export const USER_MANUAL_CONTENT = {
  pageTitle: "Manual do usuário",
  pageSubtitle:
    "O que é o Portal Suprimentos, onde ir, dúvidas frequentes e glossário mínimo.",
  backHome: "Voltar ao Início",
  tocTitle: "Nesta página",
  tocAriaLabel: "Índice do manual",
  conceptsTitle: "Conceitos que não misture",
  concepts: [
    {
      term: "Portal vs apps antigos",
      meaning:
        "O Portal reúne as jornadas. Cockpit, SC e estoque de segurança legados continuam no launcher até o cutover.",
    },
    {
      term: "Início vs Visão geral",
      meaning:
        "Início é ação e descoberta. Visão geral é o painel de KPIs do período — só aparece com acesso analítico.",
    },
    {
      term: "Filial no escopo",
      meaning:
        "Dados TOTVS respeitam as filiais liberadas para você (01 Santa Catarina, 02 Espírito Santo). Pedir outra filial não abre módulo sem capability.",
    },
  ],
  scopeNote:
    "Sem permissão (403): você não tem acesso a esta filial ou a este módulo. Peça o acesso canônico do Portal — aliases antigos sozinhos não abrem o app.",
  sections: [
    {
      id: "want",
      title: "Quero… → vá em…",
      intro: "Use esta tabela como mapa. Atalhos também estão no Início (favoritos, recentes e busca).",
      links: [
        {
          want: "Ver o que precisa de atenção",
          where: "Início",
          how: "Bloco Atenção e atalhos do catálogo",
        },
        {
          want: "Ver indicadores do período",
          where: "Visão geral",
          how: "Ou fichas de indicadores — números live entram nas próximas jornadas",
        },
        {
          want: "Abrir solicitações de compras (SC)",
          where: "Solicitações de compras",
          how: "Lista e detalhe no escopo de CC/filial; exportação CSV se tiver permissão",
        },
        {
          want: "Ver estoque de segurança (ESTSEG)",
          where: "Estoque de segurança",
          how: "Déficit e cobertura — não é o saldo físico",
        },
        {
          want: "Consultar item / produto",
          where: "Produtos",
          how: "Busca e ficha 360 quando liberada",
        },
        {
          want: "Consultar fornecedor",
          where: "Fornecedores",
          how: "Busca e ficha 360 quando liberada",
        },
        {
          want: "Acompanhar pedidos e entregas",
          where: "Pedidos de compra",
          how: "Ou Entregas para atrasos operacionais",
        },
        {
          want: "Fila pessoal",
          where: "Minhas tarefas",
          how: "Acompanhamentos atribuídos a você",
        },
        {
          want: "Administrar escopos",
          where: "Administração",
          how: "Só com permissão de administrar o Portal",
        },
      ],
    },
    {
      id: "screens",
      title: "Mapa das áreas",
      bullets: [
        "Início — atenção, busca, favoritos e caminhos por capability.",
        "Visão geral — cockpit de KPIs do período (não é a tela inicial).",
        "Solicitações de compras — lista/detalhe no escopo CC+filial; exportação CSV com permissão separada.",
        "Operações — pedidos, entregas, fornecedores, produtos, estoque e ESTSEG.",
        "Indicadores / Negociações — recorte analítico quando liberado.",
        "Administração — mappings e configurações.",
        "Ajuda — este manual, FAQ e glossário.",
      ],
    },
    {
      id: "faq",
      title: "Perguntas frequentes",
      faqs: [
        {
          q: "Qual a diferença entre estoque e estoque de segurança?",
          a: "Estoque é o saldo físico/posições. Estoque de segurança (ESTSEG) é a cobertura mínima planejada e o déficit — abra Estoque de segurança, não Estoque.",
        },
        {
          q: "OTD é a mesma coisa que atraso?",
          a: "Não. OTD mede pontualidade no período. Atrasos do dia aparecem em Entregas / operação — não use um como substituto do outro.",
        },
        {
          q: "Os indicadores do Sheets são os mesmos do Portal?",
          a: "Não automaticamente. O Portal usa indicadores homologados nas fichas e na Visão geral; planilhas externas podem divergir até a paridade.",
        },
        {
          q: "Onde vejo o significado de cada KPI da Visão geral?",
          a: "Nas fichas de indicadores e na Visão geral. Cada card mostra se o valor é intervalo, snapshot ou estado atual — não misture com o Início.",
        },
        {
          q: "Por que a lista de SC vem vazia?",
          a: "Sem centros de custo liberados e sem visão ampla, o Portal mantém fail-closed (zero registros). Peça escopo de CC ou a capability de visão ampla ao administrador.",
        },
        {
          q: "Por que não vejo Exportar CSV?",
          a: "A exportação exige a permissão de exportação além do acesso às solicitações. Ter só a lista não libera o download.",
        },
        {
          q: "Por que um card da Visão geral aparece indisponível?",
          a: "Uma fonte auxiliar falhou. Os demais indicadores continuam utilizáveis; atualize o período/filial ou tente de novo.",
        },
        {
          q: "Por que recebi 403?",
          a: "Falta capability do módulo ou filial no seu escopo. Peça o acesso canônico do Portal ao administrador.",
        },
        {
          q: "Ainda vejo os apps antigos no launcher",
          a: "É esperado na coexistência. O Portal é o hub novo; os legados só saem após cutover homologado.",
        },
      ],
    },
    {
      id: "glossary",
      title: "Glossário mínimo",
      intro: "Termos usados nas telas e nos balões de ajuda.",
      glossary: GLOSSARY_CONTENT,
    },
  ] satisfies readonly UserManualSection[],
} as const;
