/** Textos dos balões de explicação — PT de negócio, sem path técnico. */
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
  homeVsOverview:
    "Início é ação e descoberta. Visão geral é o painel de KPIs do período — só aparece se você tiver acesso analítico.",
  homeAttention:
    "Atalhos autorizados para o que precisa de ação. Contagens ao vivo entram nas próximas jornadas; se este bloco falhar, os caminhos abaixo continuam disponíveis.",
  overviewTemporal:
    "Cada card tem natureza temporal própria: intervalo (OTD, CPV, economia), snapshot (estoque, críticos) ou estado atual (SC pendentes). Início não substitui este painel.",
  purchaseRequests:
    "Lista linhas de SC no escopo de centro de custo e filial. Sem CC liberado e sem visão ampla, a lista fica vazia (fail-closed). Exportação CSV exige permissão separada.",
  userProfile:
    "Perfil do Portal Suprimentos: identidade Minha DELPI, atalhos por capability e preferências (filial padrão e densidade). Diferente do /profile global do Portal host.",
  userProfilePrefs:
    "Filial padrão e densidade de tabelas valem só neste Portal. Só você edita o próprio perfil; administradores podem ler outros usuários.",
  forbiddenUnit:
    "Você não tem permissão para esta filial ou para este módulo. Peça o acesso canônico do Portal ao administrador — aliases antigos sozinhos não abrem o app.",
} as const;
