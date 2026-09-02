/**
 * Conteúdo PT-BR do Manual do usuário (página /help).
 * Espelha docs/.../MANUAL-USUARIO-PORTAL-COMERCIAL.md — atualizar os dois juntos.
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
    "Consulta rápida: onde ir no Portal Comercial e respostas às dúvidas mais comuns.",
  backHome: "Voltar ao Início",
  tocTitle: "Nesta página",
  tocAriaLabel: "Índice do manual",
  conceptsTitle: "Três conceitos (não misture)",
  concepts: [
    { term: "Pedido", meaning: "Linha em aberto — operação e fábrica." },
    { term: "Oportunidade (OV)", meaning: "Proposta comercial no Protheus (AD1010)." },
    {
      term: "Proposta (documento)",
      meaning: "Documento ADY + PDF para o cliente.",
    },
  ],
  scopeNote:
    "O chip Escopo no topo indica de quem você vê os dados (sua carteira / equipe / todas). Não é o filtro de datas da Visão geral.",
  sections: [
    {
      id: "want",
      title: "Quero… → vá em…",
      intro: "Use esta tabela como mapa. Atalhos também estão no Início (favoritos e busca).",
      links: [
        {
          want: "Ver o que precisa de atenção hoje",
          where: "Início",
          how: "Eventos, highlights e atalhos do launcher",
        },
        {
          want: "Ver atrasos de entrega",
          where: "Meus pedidos",
          how: "Chip Atraso ou atalho no Início",
        },
        {
          want: "Ver o que pode faturar",
          where: "Meus pedidos",
          how: "Filtro de estoque / Pode faturar (alocação FIFO)",
        },
        {
          want: "Acompanhar linha ou OP",
          where: "Meus pedidos → linha",
          how: "Abra a ficha; depois a OP, se houver",
        },
        {
          want: "Ver meus clientes",
          where: "Minha Carteira",
          how: "Busca, Foco e Tendência",
        },
        {
          want: "Preparar visita ou call",
          where: "Minha Carteira → Conta",
          how: "Abas Resumo, Pedidos, Histórico, Oportunidades, Contatos, Atividades",
        },
        {
          want: "Follow-up com prazo",
          where: "Minhas tarefas",
          how: "Buckets e criar tarefa com responsável",
        },
        {
          want: "Conversar com o time",
          where: "Sala de interação",
          how: "Inbox ou painel na ficha do pedido/conta/OV",
        },
        {
          want: "Indicadores do período",
          where: "Visão geral",
          how: "Período, unidade SC/ES, KPIs e gráficos",
        },
        {
          want: "Pontualidade (OTD)",
          where: "Início → Pontualidade (OTD)",
          how: "Ou drill a partir da Visão geral",
        },
        {
          want: "Oportunidades (OV)",
          where: "Início → Oportunidades",
          how: "Lista global; clique abre a ficha",
        },
        {
          want: "PDF / documento de proposta",
          where: "Início → Propostas",
          how: "Documento ADY (não é a lista de OV)",
        },
        {
          want: "Administrar carteiras",
          where: "Administração",
          how: "Só com permissão de administrar",
        },
      ],
    },
    {
      id: "screens",
      title: "Mapa das telas",
      bullets: [
        "Início — hub: eventos + caminhos (favoritos, recentes, busca).",
        "Visão geral — placar do período (ROL, meta, conversão, carteira aberta…).",
        "Meus pedidos — bancada operacional; URL compartilhável com filtros.",
        "Minha Carteira — clientes vinculados; clique abre a Conta.",
        "Minhas tarefas — fila de follow-ups.",
        "Sala de interação — conversas internas.",
        "Administração — carteiras, equipe e grupos (gestores).",
        "OTD, Oportunidades e Propostas — pelo Início ou drills; não ficam no menu de cima.",
      ],
    },
    {
      id: "faq-access",
      title: "Dúvidas — acesso e o que eu vejo",
      faqs: [
        {
          q: "Não vejo Minha Carteira no menu",
          a: "Você tem acesso ao Portal, mas ainda não está vinculado a nenhuma carteira. Peça ao administrador do Comercial para incluí-lo como membro.",
        },
        {
          q: "Vejo pedidos de clientes que não são meus",
          a: "Sem vínculo de carteira a lista pode vir consolidada. Com carteira, o Escopo filtra. Administradores veem todas.",
        },
        {
          q: "Não vejo Administração",
          a: "Só quem tem permissão de administrar o Portal. O uso do dia a dia não precisa disso.",
        },
        {
          q: "O chip Escopo muda o mês do gráfico?",
          a: "Não. Escopo = carteira(s). Período = filtros da Visão geral (ou da tela em que você está).",
        },
      ],
    },
    {
      id: "faq-kpi",
      title: "Dúvidas — indicadores",
      faqs: [
        {
          q: "Onde vejo o ROL do mês?",
          a: "Na Visão geral — não no Início (o Início é para ação, não para o placar completo).",
        },
        {
          q: "Por que a meta aparece parcial?",
          a: "A meta do período é proporcional aos dias do intervalo. Mês incompleto não usa a meta cheia do mês.",
        },
        {
          q: "Posso somar carteira aberta com o ROL?",
          a: "Não. ROL é faturamento no período; carteira aberta é o que ainda está em aberto agora.",
        },
        {
          q: "Cadê o GR / telão de vendas?",
          a: "É o app TV Dashboard, não uma tela dentro do Portal Comercial.",
        },
      ],
    },
    {
      id: "faq-orders",
      title: "Dúvidas — pedidos e estoque",
      faqs: [
        {
          q: "No Protheus tem estoque, mas aqui diz sem ou parcial",
          a: "O Portal aloca estoque em ordem FIFO entre as linhas. O saldo pode estar comprometido por outro pedido.",
        },
        {
          q: "Pedido, OV e Proposta são a mesma coisa?",
          a: "Não. Pedido = operação; OV = oportunidade; Proposta = documento/PDF.",
        },
        {
          q: "Não recebi aviso de Pronto para faturar",
          a: "Quem recebe o aviso precisa da permissão de notificação de faturamento. Ser membro da carteira sozinho não garante o aviso.",
        },
      ],
    },
    {
      id: "faq-portfolio",
      title: "Dúvidas — carteira e conta",
      faqs: [
        {
          q: "Cliente sem pedido some da Minha Carteira?",
          a: "Não. A lista é a carteira vinculada; pedido aberto é informação extra.",
        },
        {
          q: "O que é o badge Compartilhado?",
          a: "O cliente está em mais de uma carteira ativa.",
        },
        {
          q: "Posso editar o contato do Protheus?",
          a: "Não. Cadastre contatos locais na aba Contatos da Conta.",
        },
      ],
    },
    {
      id: "who",
      title: "Quem pedir ajuda",
      bullets: [
        "Não entro no Portal / erro de permissão → TI ou Admin Minha Delpi.",
        "Não estou na carteira / clientes errados → Administrador do Portal Comercial (Administração → Carteiras).",
        "Quero aviso de faturar → Admin libera a permissão de notificação + confira preferências Minha Delpi.",
        "Número de ROL/meta estranho → gestor e quem calibra metas nos Indicadores Estratégicos.",
        "Dúvida de processo comercial → supervisor ou Sala de interação do time.",
      ],
    },
    {
      id: "glossary",
      title: "Glossário curto",
      glossary: [
        { term: "Carteira", meaning: "Clientes + membros (vendedores) no Delpi." },
        { term: "Membership", meaning: "Você está vinculado a uma carteira." },
        { term: "Escopo", meaning: "Filtro de “de quem” (própria / equipe / todas)." },
        { term: "ROL", meaning: "Receita / faturamento nos indicadores comerciais." },
        { term: "Meta", meaning: "Meta do Indicadores Estratégicos, proporcional ao período." },
        { term: "OTD", meaning: "Pontualidade: faturamento vs. data prometida." },
        { term: "FIFO", meaning: "Estoque alocado do mais antigo para o mais novo entre pedidos." },
        { term: "SC / ES", meaning: "Unidades (filiais) nos filtros." },
      ],
    },
  ] satisfies readonly UserManualSection[],
} as const;
