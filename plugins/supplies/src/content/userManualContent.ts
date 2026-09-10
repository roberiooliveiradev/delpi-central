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
    {
      term: "Perfil do Portal vs perfil Minha DELPI",
      meaning:
        "O avatar na TopBar mostra a foto do Meu Perfil (Core) e abre o perfil do Portal Suprimentos (filial padrão, densidade, units). Foto, cargo e contatos editam-se em /profile do host; preferências deste Portal editam-se no perfil do plugin.",
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
          how: "Filtros Hoje/Esta semana/Este mês… e Unidade (MultiSelect SC/ES); KPIs com Meta parcial ≠ Meta mês quando o SI distingue; Nota IDD do SI",
        },
        {
          want: "Ver OTD com velocímetro",
          where: "OTD",
          how: "Velocímetros por unidade e série no tempo; mesmos filtros da Visão geral. Diferente de Entregas (atrasos do dia)",
        },
        {
          want: "Compartilhar o mesmo recorte da Visão geral",
          where: "Visão geral",
          how: "A URL guarda unidade(s), datas e preset — copie o link com o filtro ativo",
        },
        {
          want: "Abrir solicitações de compras (SC)",
          where: "Solicitações de compras",
          how: "Lista e detalhe no escopo de CC/filial; exportação CSV se tiver permissão",
        },
        {
          want: "Alterar filial padrão ou densidade das tabelas",
          where: "Perfil (avatar na TopBar)",
          how: "Só no próprio perfil; administradores podem ler outros usuários, sem editar prefs",
        },
        {
          want: "Fixar atalhos que uso sempre",
          where: "Favoritos (estrela na TopBar ou nos caminhos)",
          how: "Clique na estrela de um caminho no Início; abra a lista pelo botão Favoritos ao lado da busca",
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
        "OTD — velocímetros de pontualidade e evolução; abra pelo Início, catálogo Análises ou CTA da Visão geral.",
        "Solicitações de compras — lista/detalhe no escopo CC+filial; exportação CSV com permissão separada.",
        "Operações — pedidos, entregas, fornecedores, produtos, estoque e ESTSEG.",
        "Indicadores / Negociações — recorte analítico quando liberado.",
        "Administração — mappings e configurações.",
        "Perfil — avatar na TopBar (foto da Core); preferências do Portal (filial padrão e densidade); foto/cargo/contatos no /profile do host.",
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
          q: "Qual a diferença entre Visão geral e a página OTD?",
          a: "A Visão geral é o placar de KPIs do período (com série OTD). A página OTD mostra velocímetros por unidade (Santa Catarina / Espírito Santo) e a evolução no tempo. Ambas usam o mesmo filtro de Unidade e período.",
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
          a: "Uma fonte auxiliar falhou. Os demais indicadores continuam utilizáveis; atualize o período/unidade ou tente de novo.",
        },
        {
          q: "O que mostra o gráfico OTD na Visão geral?",
          a: "A evolução do OTD de pedidos de compra no mesmo filtro de Unidade e período dos KPIs, com granularidade e exportação. Os velocímetros ficam na página OTD. Se a série falhar, o restante da página continua utilizável.",
        },
        {
          q: "Como filtro Unidade e período na Visão geral?",
          a: "Use o preset (Hoje, Esta semana, Este mês, trimestre, ano…) ou as datas De/Até e o MultiSelect Unidade (Santa Catarina / Espírito Santo). Vazio ou ambas = consolidado. O link da página guarda o recorte para compartilhar (F5/voltar).",
        },
        {
          q: "Por que Meta parcial e Meta mês podem ser diferentes?",
          a: "A Meta do período (parcial) é a comparable_goal do Strategic Indicators para o recorte De–Até. A Meta mês/referência é a meta cadastrada (goal_value). A Nota IDD é o score do SI — o Portal não recalcula no navegador. SC pendentes e materiais críticos não têm meta SI.",
        },
        {
          q: "Por que recebi 403?",
          a: "Falta capability do módulo ou filial no seu escopo. Peça o acesso canônico do Portal ao administrador.",
        },
        {
          q: "Onde altero a filial padrão ou a densidade das tabelas?",
          a: "No perfil do Portal Suprimentos: clique no avatar/nome na TopBar. Não existe página /preferences separada. O /profile do host Minha DELPI é outra tela (identidade global).",
        },
        {
          q: "Qual a diferença entre o perfil do Portal e o /profile da Minha DELPI?",
          a: "O perfil do plugin mostra a identidade global (foto, cargo e contatos da Core, só leitura) e guarda preferências deste Portal (units, capabilities, filial padrão, densidade). Foto/cargo/contatos editam-se em /profile do host; prefs de Suprimentos editam-se no avatar do plugin.",
        },
        {
          q: "Alterei a foto no Meu Perfil e o Suprimentos não mudou?",
          a: "A TopBar e o perfil do Portal recarregam da Core ao salvar no Meu Perfil (mesmo navegador). Se ainda estiver antiga, atualize a página do Portal Suprimentos.",
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
