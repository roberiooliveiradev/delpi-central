import {
  USER_MANUAL_TERM_CATALOG,
  type UserManualTermGroup,
} from "./userManualTermCatalog";

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
  glossaryGroups?: readonly UserManualTermGroup[];
};

export const USER_MANUAL_CONTENT = {
  pageTitle: "Manual do usuário",
  pageSubtitle:
    "Consulta rápida: onde ir no Portal Comercial, dúvidas frequentes e o catálogo de termos usados nas telas e nos ?.",
  backHome: "Voltar ao Início",
  tocTitle: "Nesta página",
  tocAriaLabel: "Índice do manual",
  conceptsTitle: "Três conceitos (não misture)",
  concepts: [
    {
      term: "Pedido",
      meaning: "Linha em aberto — operação e fábrica (veja em Meus pedidos).",
    },
    {
      term: "Oportunidade (OV)",
      meaning: "Proposta comercial no Protheus (AD1010) — lista em Oportunidades.",
    },
    {
      term: "Proposta (documento)",
      meaning: "Documento ADY + PDF para o cliente — tela Propostas.",
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
          want: "Ver mix de produto do faturamento",
          where: "Minha Carteira → Faturamento",
          how: "Filtros de período/cliente/família/produto/mercado; tabela abaixo do gráfico; personalize colunas e exporte",
        },
        {
          want: "Ver ABC de clientes",
          where: "Minha Carteira → ABC",
          how: "Mesmos filtros do Faturamento; tabela com avatar, CNPJ e participação; personalize colunas e exporte",
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
          how: "Visão: Por colaborador (resumo; clique filtra a lista) ou Por oportunidade (Busca e Status no hero). Colunas/fonte/export na toolbar. Status não altera o resumo.",
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
        {
          want: "Configurar prazos (SLA)",
          where: "Administração → SLAs",
          how: "Criar, editar ou desativar políticas de prazo (tarefa, amostra, confirmação, etapa de oferta). Soft deactivate — não apaga o histórico.",
        },
        {
          want: "Saber o que significa um termo",
          where: "Ajuda",
          how: "Catálogo de termos (definição e onde aparece)",
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
        "Minha Carteira — clientes vinculados; painéis Faturamento (série + mix), ABC, Ranking e Clientes; clique no cliente abre a Conta.",
        "Minhas tarefas — fila de follow-ups.",
        "Sala de interação — conversas internas.",
        "Administração — carteiras, equipe, grupos e SLAs (gestores).",
        "OTD, Oportunidades e Propostas — pelo Início ou drills; não ficam no menu de cima. Em Oportunidades, use Visão (colaborador | oportunidade) como na Minha Carteira.",
      ],
    },
    {
      id: "faq-access",
      title: "Dúvidas — acesso e o que eu vejo",
      faqs: [
        {
          q: "Como troco a Visão em Oportunidades?",
          a: "No hero da página: Visão → Por colaborador ou Por oportunidade. A URL guarda ?view= para compartilhar. Clique num vendedor no resumo abre a lista filtrada daquele colaborador.",
        },
        {
          q: "O Status da lista muda o resumo Por colaborador?",
          a: "Não. O resumo usa só os filtros compartilhados do hero (período, unidade, segmento, carteira…). Busca e Status aparecem no hero só na Visão Por oportunidade e não afetam o resumo.",
        },
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
          q: "Onde configuro os SLAs?",
          a: "Administração → SLAs. Cadastre políticas após homologar os prazos com as áreas. Desativar é soft (a política some dos novos cálculos; você pode reativar editando Ativa).",
        },
        {
          q: "O chip Escopo muda o mês do gráfico?",
          a: "Não. Escopo = carteira(s). Período = filtros da Visão geral (ou da tela em que você está).",
        },
        {
          q: "O filtro de clientes da Visão geral lista todos os clientes do TOTVS?",
          a: "Não. A lista vem das carteiras do recorte (ou de todas as carteiras ativas, se você não filtrar carteira). Vazio = todos os clientes daquele recorte.",
        },
        {
          q: "ABC de clientes é o mesmo que Ranking?",
          a: "Não. O painel ABC ordena por participação no período (avatar, CNPJ e praça). O painel Ranking mostra crescimento ou queda versus o mesmo período no ano anterior.",
        },
        {
          q: "Como exporto o mix de produto do faturamento?",
          a: "Minha Carteira → Faturamento. No hero: chips de Período e Mercado; cliente, família, produto e carteira na barra (como em Clientes). Excel na tabela abaixo do gráfico.",
        },
        {
          q: "Como exporto o ABC de clientes?",
          a: "Minha Carteira → ABC. Mesmos filtros do Faturamento no hero; use Excel na tabela do painel.",
        },
        {
          q: "Os filtros mudam ao trocar Faturamento, ABC, Ranking e Clientes?",
          a: "Sim. O label Visão (com help e ícones) troca o painel; cada um mostra chips de ação e barra de filtros no padrão de Clientes. Natureza e escopo de carteira ficam compartilhados.",
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
          q: "No consolidado (unidade Todas) a Visão geral mostra meta?",
          a: "Sim. Realizado e meta agregam Santa Catarina + Espírito Santo pelo método dos Indicadores Estratégicos (SI): em R$ a META MÊS é a soma das metas do mês das filiais e a META PARCIAL aplica a fração do período uma vez; em % a meta consolidada é média. Não é soma inventada no Portal. Se a agregação não for possível, aparece o aviso para filtrar uma unidade.",
        },
        {
          q: "Posso somar carteira aberta com o ROL?",
          a: "Não. ROL é faturamento no período; carteira aberta é o que ainda está em aberto agora.",
        },
        {
          q: "Como vejo o histórico em quantidade (não em R$)?",
          a: "Minha Carteira → Faturamento: use o toggle Métrica R$ | Qtd. A série e o mix por produto passam a usar quantidade fornecida. UMs mistas aparecem sem conversão automática.",
        },
        {
          q: "A linha de tendência distorce no mês corrente?",
          a: "Por padrão a tendência exclui o bucket incompleto (ex.: mês em andamento). Nos overlays do gráfico, «Ponderar período parcial» inclui o valor escalado pelo % do período já decorrido.",
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
          q: "Qual a diferença entre data de entrega, despacho e previsão OP?",
          a: "Data de entrega é o compromisso da linha, interpretado pelo Incoterm: se o cliente busca (EXW ou FOB), é a data na expedição; se a Delpi entrega (CIF), é a data de saída da empresa. Despacho é a saída registrada da fábrica, quando houver. Previsão OP é a disponibilidade pela produção — o badge compara essa previsão com a data de entrega.",
        },
        {
          q: "Posso ver quantidade em peças em vez de milheiro?",
          a: "Sim. Em Meus pedidos e na Conta (itens da NF) use Milheiro | Peças. Só converte quando a UM é MI (1 MI = 1000 PC) — é só apresentação; o contrato da API não muda.",
        },
        {
          q: "Onde vejo a data de colocação do pedido ou o lead time até o faturamento?",
          a: "Ainda não. Essas datas e o ciclo completo ficam para o CRM — nas tabelas atuais de OV/pedido não há data de colocação confiável homologada.",
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
        "Não estou na carteira / clientes errados → Administrador do Portal Comercial (Administração).",
        "Quero aviso de faturar → Admin libera a permissão de notificação + confira preferências Minha Delpi.",
        "Número de ROL/meta estranho → gestor e quem calibra metas nos Indicadores Estratégicos.",
        "Dúvida de processo comercial → supervisor ou Sala de interação do time.",
      ],
    },
    {
      id: "glossary",
      title: "Catálogo de termos",
      intro:
        "Significados já usados no Portal e nos ? das telas. «Onde aparece» é a aplicação. Os mesmos textos dos helps — sem inventar outro glossário.",
      glossaryGroups: USER_MANUAL_TERM_CATALOG,
    },
  ] satisfies readonly UserManualSection[],
} as const;
