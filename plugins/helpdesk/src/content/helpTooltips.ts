/** Ajuda in-app do Meus Chamados — textos curtos (1 frase) para tooltip. */

export const helpTooltips = {
  list: "Chamados de TI no seu nome. Use tabela ou cards, filtros, ordenação e paginação; o + abre um novo.",
  link: "Na primeira vez, autorize o helpdesk com o mesmo login da Minha DELPI para ver seus chamados.",
  create:
    "Título e descrição; à direita categoria, urgência, técnico (se permitido) e observadores. O rascunho sobrevive ao F5.",
  detail:
    "Conversa do chamado. Responda no rodapé enquanto estiver aberto; solução e arquivos aparecem no fio.",

  createUi: {
    back: "Volta à lista com o mesmo recorte, sem gravar este formulário.",
    title: "Assunto curto do chamado. Obrigatório.",
    description:
      "Formatação, @ para mencionar, clipe, colar ou arrastar. Arraste o canto da imagem para redimensionar.",
    attach: "Anexa por clipe ou arrastar. Na abertura, o envio sobe depois de criar o chamado.",
    category: "Categoria visível para você no helpdesk. Obrigatória.",
    urgency: "Urgência do chamado. Obrigatória.",
    assignee: "Opcional. Busque por nome ou e-mail na Minha DELPI; só entram pessoas com conta no helpdesk.",
    observers: "Opcional. IDs de usuário do helpdesk, separados por vírgula (só observador).",
    send: "Grava o chamado no seu nome e abre a conversa.",
  },

  detailUi: {
    back: "Volta à lista com o mesmo recorte (filtros e página).",
    reply:
      "Formatação, @ para mencionar, clipe, colar ou arrastar. Arraste o canto da imagem para redimensionar.",
    attach: "Anexa por clipe ou arrastar; imagem entra no texto da resposta.",
    send: "Grava o acompanhamento público. Em chamado fechado o botão some.",
    assignee: "Busque o responsável por nome ou e-mail na Minha DELPI. Só aparece se o helpdesk permitir atribuir no seu perfil.",
    assigneeAction: "Grava a atribuição ou reatribuição neste chamado.",
    openInGlpi: "Abre este chamado no helpdesk (GLPI) para fluxos que ainda não estão na Minha DELPI.",
    acceptSolution: "Aceita a solução e fecha o chamado no helpdesk.",
    rejectSolution: "Recusa a solução e reabre o chamado para novo atendimento.",
    submitSatisfaction: "Envia sua nota de 1 a 5 e o comentário opcional.",
    acceptValidation: "Aceita a etapa de aprovação deste chamado.",
    rejectValidation: "Recusa a etapa de aprovação deste chamado.",
    attachments: "Arquivos ligados ao chamado. Clique para prévia ou baixar.",
  },

  listUi: {
    refreshPage: "Atualiza a lista com o mesmo recorte da URL.",
    openTicket: "Abre o formulário de um chamado novo no seu nome.",
    clearFilters: "Remove o recorte; mantém ordenação e tamanho da página.",
    viewLayout: "Alterna tabela e cards. A escolha fica neste navegador.",
    pageSize: "Quantos chamados por página: 10, 20 ou 50.",
    sortChip: "Ordenação ativa (até três níveis).",
    filterChip: "Critério do recorte gravado na URL (sobrevive ao F5).",
    filterBuilderToggle: "Abre o construtor de filtros com regras E (AND).",
    sortBuilderToggle: "Abre a ordenação em até três níveis.",
    columns: "Mostra ou esconde colunas da tabela. Preferência neste navegador.",
    refreshList: "Atualiza a grade sem limpar filtros.",
  },

  pagination: {
    nav: "Navegue entre páginas. O helpdesk não informa o total exato de chamados.",
    jumpEmpty: "Informe um número de página.",
    jumpInvalid: "Use apenas números inteiros.",
    jumpBelowMin: "A página mínima é 1.",
  },

  filterBuilder: {
    panel: "Monte regras com E (AND). Ao aplicar, o recorte vai para a URL.",
    field: "Campo do filtro aceito nesta lista.",
    operator: "Operação: contém, é, de ou até — conforme o campo.",
    value: "Valor da regra. Vazio não entra ao aplicar.",
    removeRule: "Remove esta regra. A lista só muda depois de Aplicar.",
    addRule: "Inclui outra regra E.",
    clear: "Apaga as regras do painel sem mudar a URL até aplicar.",
    apply: "Grava as regras na URL e recarrega a lista.",
  },

  sortBuilder: {
    panel: "Até três níveis. O primeiro é o que a grade destaca.",
    field: "Campo deste nível de ordenação.",
    direction: "Ascendente (A→Z) ou descendente.",
    removeLevel: "Remove este nível (precisa restar pelo menos um).",
    addLevel: "Inclui outro nível (máximo três).",
    apply: "Grava a ordenação na URL e recarrega a lista.",
  },

  columns: {
    id: "Número do chamado no helpdesk.",
    title: "Título informado na abertura.",
    status: "Estado atual no helpdesk.",
    category: "Categoria do chamado.",
    urgency: "Urgência cadastrada.",
    assigned: "Técnico atribuído, quando houver.",
    created_at: "Data e hora de abertura.",
    updated_at: "Data e hora da última alteração.",
    solved_at: "Data e hora da solução, quando houver.",
    closed_at: "Data e hora do fechamento, quando houver.",
    requester: "Nome do solicitante (rótulo).",
  },
} as const;
