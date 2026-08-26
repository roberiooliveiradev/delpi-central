/** Catálogo central de helps do portal Manutenção (hover no rótulo). */
export const DM_HELP = {
  shell: {
    navHome: "Volta ao início do módulo Manutenção.",
    navFiliais: "Cadastro de filiais operacionais do módulo.",
    navMiniAplicadores: "Reposição de peças, golpes e alertas preventivos.",
    navProgramas: "Ranking e cadastro de produtos para programas de máquina.",
    navManutencaoGeral: "Formulário de registro de máquinas, equipamentos e lâmpadas.",
  },
  home: {
    title: "Escolha a filial e um submódulo para continuar.",
    comecar: "Atalhos para os submódulos disponíveis na filial selecionada.",
  },
  filiais: {
    title: "Cadastro de filiais operacionais (código TOTVS e nome exibido).",
    codigo: "Código da filial no TOTVS (ex.: 01, 02).",
    nome: "Nome exibido nas telas do módulo.",
  },
  miniAplicadores: {
    listaTitle: "Ferramentas de mini-aplicadores cadastradas no TOTVS.",
    peca: "Código da peça (3019…) vinculada à reposição.",
    dataReposicao: "Data e hora em que a peça foi reposta na ferramenta.",
    dataUltima: "Data da reposição anterior desta peça (referência de golpes).",
    golpes: "Quantidade de golpes registrados desde a última reposição.",
    sugerirGolpes: "Consulta o TOTVS e preenche golpes com base no período.",
    motivo: "Motivo da troca cadastrado em Configuração.",
    observacao: "Observação livre sobre a reposição.",
    historico: "Reposições anteriores desta ferramenta.",
    indicadores: "Indicadores consolidados das reposições registradas.",
    indicadoresTotal: "Quantidade de reposições registradas para esta ferramenta.",
    indicadoresPecasDistintas: "Número de códigos de peça distintos trocados.",
    indicadoresMediaGolpes: "Média de golpes entre reposições.",
    indicadoresUltimaReposicao: "Data da reposição mais recente.",
    chartGolpes: "Evolução de golpes por reposição e peça.",
    componentesEstoque: "Componentes da ferramenta e saldo nos armazéns 01 e 99.",
    componentesArvore:
      "Visão hierárquica da estrutura (níveis indentados) com saldos 01 e 99 por componente.",
    estoque01: "Saldo no almoxarifado (local 01).",
    estoque99: "Saldo na fábrica (local 99).",
    buscaPeca: "Busca peças 3019 por código ou descrição.",
    ondeUsado: "Produtos que utilizam componentes desta ferramenta.",
    auditoria: "Histórico de alterações registradas no módulo.",
  },
  relatorio: {
    title: "Ranking preventivo por golpes, revisões e últimas reposições.",
    kpiCritico: "Pares ferramenta/peça classificados como CRÍTICO.",
    kpiAtencao: "Pares em ATENÇÃO — próximos do limite configurado.",
    kpiOk: "Pares dentro do limite OK.",
    kpiRevisao: "Ferramentas com revisão programada pendente ou vencida.",
    kpiRevisaoVencida: "Ferramentas com revisão programada vencida.",
    kpiRevisaoAtencao: "Ferramentas com revisão próxima do prazo.",
    kpiRevisaoOk: "Ferramentas com revisão dentro do prazo.",
    kpiFerramentasProgramadas: "Total de ferramentas com revisão programada na filial.",
    kpiParesMonitorados: "Pares ferramenta/peça monitorados no ranking preventivo.",
    filtroFerramenta: "Filtra por código ou descrição da ferramenta.",
    tabRanking: "Ranking preventivo por percentual de uso em relação à média histórica.",
    tabRevisoesTable: "Alertas de revisão programada por ferramenta.",
    tabUltimasTable: "Últimas reposições registradas na filial.",
    filtroPeca: "Filtra por código da peça.",
    rankingUsoVisual: "Barra esquerda = média histórica de golpes; direita = golpes atuais.",
    rankingHistoricoVisual: "Série temporal de golpes registrados em cada reposição.",
    tabAlertas: "Ranking preventivo por percentual de uso.",
    tabRevisoes: "Alertas de revisão programada.",
    tabUltimas: "Últimas reposições registradas.",
    tabDetalhe: "Detalhe operacional do par selecionado.",
  },
  configuracao: {
    motivoDescricao:
      "Nome do motivo de troca usado no histórico de reposições (ex.: desgaste, quebra, ajuste).",
    excluirPreventiva:
      "Reposições com este motivo não entram na média de golpes nem no ranking preventivo da peça.",
    statusDescricao:
      "Rótulo exibido no relatório preventivo quando a regra for atendida (ex.: CRÍTICO, ATENÇÃO, OK).",
    statusOperador:
      "Compara o percentual de uso atual com a média histórica de golpes entre reposições.",
    statusPercentual:
      "Limite em relação à média (ex.: 80 significa 80% da média histórica de golpes).",
    motivosSection:
      "Cadastro dos motivos disponíveis ao registrar uma reposição de peça na ferramenta.",
    statusSection:
      "Define como cada par ferramenta/peça é classificado no relatório preventivo.",
  },
  programas: {
    title: "Ranking de produtos e cadastro para programas de máquina.",
    busca: "Filtra produtos por código ou descrição.",
  },
  manutencaoGeral: {
    title: "Formulário Google para registro de máquinas, equipamentos e lâmpadas.",
  },
  revisao: {
    section:
      "Programação de revisão periódica desta ferramenta no módulo preventivo (ex.: inspeção a cada 3 meses).",
    ferramenta:
      "Código da ferramenta atual no TOTVS — a programação fica vinculada a ela na filial.",
    referencia:
      "Data da última revisão feita ou marco inicial do ciclo. Vazio usa a data de criação da programação.",
    intervalo:
      "Periodicidade em meses calendário entre revisões (1 a 120). Ex.: 3 = revisar a cada três meses.",
    observacao:
      "Nota opcional sobre o que verificar na revisão (checklist, pontos críticos, etc.).",
    registrar:
      "Marca a revisão como feita na data informada e recalcula a próxima revisão a partir dela.",
    historico:
      "Registros de revisões marcadas como feitas nesta ferramenta (a partir de agora).",
    historicoEditar:
      "Corrige a data ou observação de uma marcação feita. A referência da programação é recalculada.",
    historicoExcluir:
      "Remove a marcação do histórico e recalcula a referência com base na revisão feita mais recente.",
  },
  preventivaDetalhe: {
    historicoGolpes: "Golpes registrados em cada reposição deste par.",
    comparativo: "Comparativo entre média histórica e golpes atuais.",
  },
} as const;
