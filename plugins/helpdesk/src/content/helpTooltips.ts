/** Ajuda in-app do Meus Chamados — textos curtos (1 frase) para tooltip. */

export const helpTooltips = {
  list: "Chamados de TI no seu nome. Busque, filtre por status e abra um novo com Abrir chamado.",
  link: "Abrindo a autorização do helpdesk com o mesmo login da Minha DELPI. Se não redirecionar, use o botão.",
  create:
    "Título e descrição; à direita categoria, urgência, técnico (se permitido) e observadores. O rascunho sobrevive ao F5.",
  detail:
    "Workspace do chamado. Seletor de ação: responder, solução, tarefa, anexo ou aprovação — só o que o helpdesk liberar.",

  createUi: {
    back: "Volta à lista com o mesmo recorte, sem gravar este formulário.",
    title: "Assunto curto do chamado. Obrigatório.",
    description:
      "Formatação, @ para mencionar, clipe, colar ou arrastar. Arraste o canto da imagem para redimensionar.",
    attach: "Anexa por clipe ou arrastar. Na abertura, o envio sobe depois de criar o chamado.",
    category: "Categoria visível para você no helpdesk. Obrigatória.",
    urgency: "Urgência do chamado. Obrigatória.",
    assignee: "Opcional. Busque por nome ou e-mail (Minha DELPI e helpdesk).",
    observers: "Opcional. IDs de usuário do helpdesk, separados por vírgula (só observador).",
    send: "Grava o chamado no seu nome e abre a conversa.",
  },

  detailUi: {
    back: "Volta à lista com o mesmo recorte (filtros e página).",
    actionMenu:
      "Tipo de interação: responder, solução, tarefa, anexo ou aprovação — só o que o helpdesk liberar.",
    reply:
      "Formatação, @ para mencionar, clipe, colar ou arrastar. Arraste o canto da imagem para redimensionar.",
    createSolution: "Registre a solução deste chamado.",
    createTask: "Crie uma tarefa vinculada a este chamado.",
    requestApproval: "Solicite a aprovação deste chamado a um usuário ou grupo.",
    attach: "Anexa por clipe ou arrastar; imagem entra no texto da resposta.",
    attachFile: "Anexe arquivos ao chamado sem enviar uma mensagem.",
    send: "Envia a resposta neste chamado. Em chamado fechado o botão some.",
    assignee: "Busque o responsável por nome ou e-mail. Só aparece se o helpdesk permitir atribuir no seu perfil.",
    assigneeAction: "Grava a atribuição ou reatribuição neste chamado.",
    openInGlpi: "Abre este chamado no helpdesk (GLPI) para fluxos que ainda não estão na Minha DELPI.",
    acceptSolution: "Aceita a solução e fecha o chamado no helpdesk.",
    rejectSolution: "Recusa a solução e reabre o chamado para novo atendimento.",
    submitSatisfaction: "Envia sua nota de 1 a 5 e o comentário opcional.",
    acceptValidation: "Aceita a etapa de aprovação deste chamado.",
    rejectValidation: "Recusa a etapa de aprovação deste chamado.",
    attachments: "Arquivos ligados ao chamado. Clique para prévia ou baixar.",
    actionFields: {
      reply: {
        model:
          "Preenche a mensagem com um modelo disponível. Você pode editar antes de enviar.",
        source: "Classifica a origem deste acompanhamento. Não altera o autor da resposta.",
        message: "Texto da resposta enviada neste chamado.",
      },
      solution: {
        model:
          "Preenche a solução com um modelo disponível. Pode definir também o tipo.",
        type: "Classifica a solução para organização, pesquisa e relatórios.",
        description: "Descreva a solução proposta para este chamado.",
      },
      task: {
        model: "Preenche os campos da tarefa com um modelo disponível.",
        category: "Classifica a tarefa para organização, pesquisa e relatórios.",
        status: "Define o estado inicial da tarefa.",
        duration: "Tempo estimado para executar a tarefa, em minutos.",
        assignee: "Técnico responsável pela execução desta tarefa.",
        group: "Grupo relacionado à tarefa. Pode coexistir com o técnico responsável.",
        planning: "Permite definir início e fim previstos para a execução.",
        description: "Descreva o que deve ser feito nesta tarefa.",
        planBegin: "Data e hora de início previstas.",
        planEnd: "Data e hora de término previstas.",
      },
      attachment: {
        title:
          "Nome exibido de cada arquivo. Se vazio, usa o nome original. Com vários arquivos, o mesmo título vale para todos.",
        files: "Selecione um ou mais arquivos para anexar ao chamado.",
      },
      approval: {
        model: "Preenche o comentário da solicitação com um modelo disponível.",
        approverType: "Escolha se a aprovação será solicitada a um usuário ou a um grupo.",
        approver: "Pessoa que deverá analisar e responder à solicitação.",
        group: "Grupo ao qual a solicitação de aprovação será enviada.",
        message: "Contexto opcional para ajudar na decisão de aprovação.",
      },
    },
  },

  listUi: {
    refreshPage: "Atualiza a lista com o mesmo recorte da URL.",
    openTicket: "Abre o formulário de um chamado novo no seu nome.",
    clearFilters: "Remove o recorte; mantém ordenação e tamanho da página.",
    viewLayout: "Alterna tabela e cards no desktop. Em telas estreitas a lista usa cards automaticamente.",
    pageSize: "Quantos chamados por página: 10, 20 ou 50.",
    sortChip: "Ordenação ativa (até três níveis).",
    filterChip: "Critério do recorte gravado na URL (sobrevive ao F5).",
    filterBuilderToggle: "Abre filtros avançados em um painel junto ao botão.",
    sortBuilderToggle: "Abre a ordenação em um painel junto ao botão.",
    columns: "Mostra ou esconde colunas da tabela. Preferência neste navegador.",
    refreshList: "Atualiza a grade sem limpar filtros.",
    search: "Busca no número, título ou conteúdo do chamado.",
    statusChips: "Atalho de status. Sem contadores — o helpdesk não expõe totais por estado.",
    advancedFilters: "Refine os chamados com critérios adicionais.",
  },

  pagination: {
    nav: "Navegue entre páginas. O helpdesk não informa o total exato de chamados.",
    jumpEmpty: "Informe um número de página.",
    jumpInvalid: "Use apenas números inteiros.",
    jumpBelowMin: "A página mínima é 1.",
  },

  filterBuilder: {
    panel: "Refine os chamados com um ou mais critérios.",
    field: "Campo do filtro aceito nesta lista.",
    operator: "Operação: contém, é, de ou até — conforme o campo.",
    value: "Valor da regra. Vazio não entra ao aplicar.",
    removeRule: "Remove esta regra. A lista só muda depois de Aplicar.",
    addRule: "Inclui outro critério.",
    clear: "Apaga as regras do painel sem mudar a URL até aplicar.",
    apply: "Aplica os critérios e atualiza a lista.",
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
