/** Textos dos balões de explicação — PT de negócio, sem path técnico. */

const HOME_HELP = {
  vsOverview:
    "Início é ação e descoberta. Visão geral é o painel de KPIs do período — só aparece se você tiver acesso analítico.",
  attention:
    "Atalhos autorizados para o que precisa de ação. Contagens ao vivo entram nas próximas jornadas; se este bloco falhar, os caminhos abaixo continuam disponíveis.",
  paths:
    "Caminhos por seção liberados para o seu acesso. Busque, fixe favoritos e reabra os últimos acessos. Objetivo: chegar à ação em poucos cliques.",
  search:
    "Filtra seções e rotas do catálogo pelo nome ou palavras-chave. Também dá para buscar na barra superior (Ctrl/Cmd+K).",
  favorites:
    "Atalhos que você fixou com a estrela nos caminhos. Ficam neste navegador e só mostram áreas ainda liberadas para você.",
  recents:
    "Últimas áreas abertas neste navegador. A lista respeita as permissões atuais.",
  queueOk:
    "Nenhum atalho de atenção pendente no momento. Os caminhos e a busca abaixo continuam disponíveis.",
  heroAttention:
    "Quantidade de atalhos de atenção disponíveis agora. «Em dia» significa que não há pendências neste bloco.",
  heroUnits:
    "Quantas filiais estão liberadas no seu escopo do Portal. Os dados operacionais respeitam esse limite.",
  heroOverview:
    "Atalho para a Visão geral (KPIs do período). Só aparece liberado se você tiver acesso analítico.",
  scopeBadge:
    "Filiais liberadas na sessão. Sem filial no escopo, módulos TOTVS podem vir vazios ou bloqueados.",
  sections: {
    attention:
      "Entrada do Portal e fila pessoal (Minhas tarefas) — ação do dia, sem misturar com o painel de KPIs.",
    analytics:
      "Visão geral, negociações e indicadores do período. Não substitui o bloco Atenção do Início.",
    purchase_requests:
      "Solicitações de compras no escopo de centro de custo e filial. Lista vazia pode significar falta de CC, não ausência de SC.",
    operations:
      "Pedidos, entregas, fornecedores, produtos, estoque físico e estoque de segurança (ESTSEG).",
    administration:
      "Mappings, escopos e configurações do Portal — só com permissão de administrar.",
    help: "Manual do usuário: Quero→onde, FAQ e glossário do Portal Suprimentos.",
  },
} as const;

export const SP_HELP = {
  shell: {
    navHome: "Atenção do dia, busca e atalhos para as áreas que você pode acessar.",
    navOverview:
      "Indicadores do período. Não é a tela inicial — o Início mostra o que precisa de ação.",
    navMyTasks: "Fila de acompanhamento atribuída a você.",
    navPurchaseRequests: "Solicitações de compras no seu escopo de centro de custo e filial.",
    navOperations: "Pedidos, entregas, fornecedores, produtos e estoques autorizados.",
    navAdmin: "Mappings, escopos e configurações do Portal.",
    navHelp: "O que é o Portal, diferença para os apps antigos e o que fazer em 403.",
  },
  coexistence:
    "O Portal Suprimentos reúne as jornadas. Os apps antigos (cockpit, SC, estoque de segurança) continuam no launcher até o cutover.",
  home: HOME_HELP,
  /** Alias estável para consumidores existentes. */
  homeVsOverview: HOME_HELP.vsOverview,
  homeAttention: HOME_HELP.attention,
  overviewTemporal:
    "Cada card tem natureza temporal própria: intervalo (OTD, CPV, economia), snapshot (estoque, críticos) ou estado atual (SC pendentes). Início não substitui este painel.",
  overviewFiltersPeriod:
    "Atalhos de período (este mês, trimestre, ano…). Ao mudar datas manualmente, o preset vira Personalizado.",
  overviewFiltersFrom: "Data inicial do recorte analítico compartilhado na URL.",
  overviewFiltersTo: "Data final do recorte analítico compartilhado na URL.",
  overviewFiltersBranch:
    "Unidades liberadas no seu escopo (Santa Catarina e/ou Espírito Santo). Vazio ou ambas = consolidado. Unidade fora do escopo é bloqueada pela API.",
  overviewOtdChart:
    "Série de OTD de pedidos de compra. Usa o mesmo filtro de unidade e período da Visão geral. Abra OTD para ver os velocímetros.",
  overviewCompareChart:
    "Barras valor × meta só para KPIs de intervalo que já vieram no overview — não inventa série CPV/Savings.",
  otdAnalyticsPage:
    "Pontualidade de compras com velocímetros por unidade (Santa Catarina / Espírito Santo) e evolução no tempo. Diferente da Visão geral (placar de KPIs) e de Entregas (atrasos do dia).",
  purchaseRequests:
    "Lista linhas de SC no escopo de centro de custo e filial. Sem CC liberado e sem visão ampla, a lista fica vazia (fail-closed). Exportação CSV exige permissão separada.",
  userProfile:
    "Perfil do Portal Suprimentos: identidade Minha DELPI (foto, cargo e contatos da Core, só leitura), atalhos por capability e preferências (filial padrão e densidade). Edite foto/cargo/contatos em /profile do Portal host.",
  userProfilePrefs:
    "Filial padrão e densidade de tabelas valem só neste Portal. Só você edita o próprio perfil; administradores podem ler outros usuários.",
  forbiddenUnit:
    "Você não tem permissão para esta filial ou para este módulo. Peça o acesso canônico do Portal ao administrador — aliases antigos sozinhos não abrem o app.",
} as const;
