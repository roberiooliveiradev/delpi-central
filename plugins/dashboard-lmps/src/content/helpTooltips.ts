export const LMPS_HELP_TOOLTIPS = {
  filters: {
    competence:
      "Mês de referência (aaaa-mm). Ao selecionar, ajusta o período para o mês inteiro — ou até hoje, no mês corrente. Fica vazio quando o período abrange mais de um mês.",
    dateStart:
      "Início do período. KPIs, gráficos e tabela consideram propostas com data de início a partir desta data.",
    dateEnd:
      "Fim do período. Deve ser igual ou posterior à data inicial.",
    branch:
      "Unidade TOTVS da proposta. Permite selecionar várias; vazio = todas as unidades.",
    listingType:
      "Classificação da listagem (LMP, Amostra ou Outro). Permite múltipla seleção.",
    status:
      "Status de prazo: Andamento (em aberto), Pontual/Atrasado (só após fechamento) ou Retornada. Permite múltipla seleção.",
  },
  actions: {
    pageSubtitle:
      "Resumo do escopo analítico: prazo, nível de SLA, status de classificação e lead time útil das LMPs.",
    refresh:
      "Recarrega KPIs, gráficos e tabela com os filtros atuais (período, unidade, tipo e status).",
    exportCsv:
      "Exporta os registros visíveis na tabela para CSV, respeitando filtros e busca local.",
    back:
      "Retorna ao dashboard de LMPs preservando os filtros de período e unidade na URL.",
    detailRefresh:
      "Atualiza proposta, produtos, estrutura e histórico da OV no TOTVS.",
  },
  pagination: {
    info: "Paginação client-side dos registros já carregados ou filtrados localmente.",
    previous: "Volta uma página mantendo ordenação e busca.",
    next: "Avança uma página mantendo ordenação e busca.",
  },
  kpis: {
    percentOnTime:
      "Percentual de propostas classificadas como Pontual no período e filtros aplicados.",
    avgLeadTime:
      "Média de lead time útil (dias) das propostas no recorte filtrado.",
    totalProposals:
      "Quantidade de propostas/OVs no período após filtros. Meta exibida quando configurada na API.",
  },
  charts: {
    countByLevel:
      "Distribuição das propostas por nível de SLA (Nível 1, 2 ou 3) no período filtrado.",
    countByStatus:
      "Distribuição por status de classificação de prazo (Pontual, Atrasado, etc.).",
    avgLeadByLevel:
      "Média de lead time útil em dias para cada nível de SLA.",
    evolution:
      "Evolução temporal da média de lead time útil e da quantidade de propostas. Use o agrupamento para mudar a granularidade (dia, semana, mês).",
    evolutionGranularity:
      "Agrupa os pontos do gráfico de evolução por dia, semana ou mês conforme o intervalo selecionado.",
  },
  table: {
    section:
      "Propostas do período após filtros. Clique na linha para abrir o detalhe da OV com produtos e estrutura.",
    branch: "Unidade TOTVS vinculada à proposta.",
    kind: "Tipo de listagem: LMP, Amostra ou Outro.",
    sale: "Número da proposta / ordem de venda (OV).",
    revision:
      "Revisão AD1010 usada na medição do ciclo (homologação medida ou revisão de engenharia do período).",
    cycle:
      "Índice do ciclo de trabalho no mês para a mesma OV (1 = primeiro ciclo; 2+ = reabertura ou nova revisão no período).",
    description: "Descrição comercial resumida da proposta.",
    startDate: "Data de início da proposta no TOTVS.",
    endDate: "Data de encerramento ou previsão de fim.",
    engineeringStatus: "Situação atual no fluxo de engenharia.",
    qtdPi: "Quantidade de produtos intermediários (PI) vinculados.",
    nivel: "Nível de SLA aplicado à proposta (1, 2 ou 3).",
    slaDays: "Quantidade de dias úteis previstos no SLA do nível.",
    limitDate: "Data limite calculada com base no SLA.",
    leadTime: "Lead time útil consumido (dias úteis).",
    status:
      "Andamento enquanto aberta; Pontual ou Atrasado só no fechamento; Retornada em exceção.",
  },
  detail: {
    statusKpi:
      "Status de classificação de prazo da proposta e situação resumida da engenharia.",
    leadTimeKpi:
      "Lead time útil consumido, nível de SLA e dias úteis previstos para a OV.",
    engineeringTimeKpi:
      "Tempo total em engenharia e quantidade de PI vinculados à proposta.",
    proposalSection:
      "Dados cadastrais da OV, classificação de prazo e indicadores de SLA calculados para o período filtrado.",
    engineeringSection:
      "Resumo quantitativo do fluxo de engenharia: entradas, encerramentos, avanços, retornos e tempo acumulado.",
    customerSection:
      "Identificação comercial do cliente e do vendedor responsável pela proposta no TOTVS.",
    productsSection:
      "Produtos vinculados à OV no TOTVS, com tipo, grupo e quantidade de PI por item.",
    productStructureSection:
      "Estrutura analítica (BOM) de cada produto da proposta, com níveis aninhados como no cadastro TOTVS.",
    proposalBranch: "Unidade TOTVS em que a proposta está registrada.",
    proposalKind: "Classificação da listagem: LMP, Amostra ou Outro.",
    proposalNumber: "Número da proposta / ordem de venda (OV).",
    proposalDescription: "Descrição comercial resumida cadastrada na proposta.",
    proposalStartDate: "Data de início da proposta no TOTVS.",
    proposalEndDate: "Data de encerramento ou previsão de fim da proposta.",
    proposalStatus:
      "Andamento se aberta; Pontual/Atrasado calculados só no fechamento; Retornada em exceção.",
    proposalNivel: "Nível de SLA aplicado (1, 2 ou 3) conforme regras de negócio.",
    proposalSlaDays: "Quantidade de dias úteis previstos no SLA do nível.",
    proposalLimitDate: "Data limite de entrega calculada a partir do início e do SLA.",
    proposalLeadTime: "Lead time útil já consumido, em dias úteis.",
    proposalQtdPi: "Total de produtos intermediários (PI) vinculados à proposta.",
    engineeringStatus: "Situação consolidada da proposta no fluxo de engenharia.",
    engineeringEntries:
      "Quantidade de eventos de entrada no fluxo de engenharia (última revisão medida).",
    engineeringClosed: "Eventos de engenharia encerrados no TOTVS.",
    engineeringAdvanced: "Avanços de estágio saindo do fluxo de engenharia.",
    engineeringReturned: "Retornos da proposta ao fluxo de engenharia.",
    engineeringTotalTime:
      "Soma do tempo em minutos nos eventos de engenharia da revisão medida.",
    engineeringSlaMinutes: "SLA convertido em minutos conforme o nível da proposta.",
    customerName: "Razão social ou nome do cliente vinculado à OV.",
    customerCode: "Código do cliente no cadastro TOTVS (SA1).",
    customerStore: "Loja do cliente no cadastro TOTVS.",
    sellerName: "Nome do vendedor responsável pela proposta.",
    sellerCode: "Código do vendedor no cadastro TOTVS (SA3).",
    productCode: "Código do produto no cadastro TOTVS (SB1).",
    productDescription: "Descrição comercial; referência entre parênteses quando informada.",
    productGroup: "Grupo de produtos (B1_GRUPO).",
    productType: "Tipo do item: PA, PI, MP, etc.",
    productQtdPi: "Quantidade de PI associada a este produto na proposta.",
    historySection:
      "Linha do tempo completa da OV no TOTVS (AIJ010): revisões, processos, estágios, prazos e duração de cada evento.",
    historyRevision: "Revisão da proposta vinculada ao evento.",
    historyProcess: "Processo do fluxo comercial/engenharia (código TOTVS e rótulo).",
    historyStage: "Estágio dentro do processo (ex.: engenharia, amostra, homologação).",
    historyStart: "Data e hora de início registradas para o evento.",
    historyLimit: "Data e hora limite previstas para conclusão do estágio.",
    historyEnd: "Data e hora de encerramento, quando informadas.",
    historyDuration:
      "Tempo entre início e encerramento. Eventos em aberto exibem duração acumulada até hoje.",
    historyStatus: "Status do evento no workflow TOTVS (AIJ_STATUS).",
    historyEngineering:
      "Estágios de engenharia, amostra ou homologação — inclui eventos fora dos processos 000002/000003 quando o estágio pertence ao fluxo técnico.",
    historyState:
      "Situação derivada do evento: concluído, em andamento ou atrasado em relação ao limite.",
    historyTimelineView:
      "Visualização cronológica agrupada por revisão, com destaque para o evento atual e badges de situação.",
    historyTableView:
      "Visualização tabular completa com todas as colunas do AIJ010 para consulta detalhada.",
    historyTimelineFootnote:
      "Eventos ordenados conforme o TOTVS (revisão, data/hora de início e estágio). Duração em aberto considera o momento atual.",
    historyFilterAll:
      "Histórico completo da OV em todas as revisões (inclui ciclos anteriores, ex.: 2019).",
    historyFilterEngineering:
      "Estágios técnicos do fluxo, limitados à revisão e data de início exibidas no painel LMP.",
    historyFilterOpen:
      "Eventos em aberto no AIJ010, limitados ao escopo do painel LMP (revisão/data de início).",
    historyFilterCurrentRevision:
      "Eventos da revisão AD1010 usada na linha do painel LMP, a partir da data de início exibida.",
    historyGantt:
      "Faixa proporcional dentro da revisão: barra = início até encerramento (ou hoje se em aberto); traço = data limite.",
    historyGlobalGantt:
      "Escala única com todos os eventos da OV. Cores destacam engenharia, atraso, evento atual e estágios em aberto.",
    structureTreeCode: "Código do componente na estrutura (SB1).",
    structureTreeDescription: "Descrição comercial cadastrada para o item.",
    structureTreeQuantity: "Quantidade na estrutura com unidade de medida TOTVS.",
    structureCode: "Código do componente na estrutura analítica (SB1).",
    structureDescription: "Descrição comercial do item na BOM.",
    structureType: "Tipo do material: PA, PI, MP, etc.",
    structureQuantity: "Quantidade necessária na estrutura, com unidade de medida.",
  },
  tableSearch:
    "Filtra os registros da tabela pelo texto digitado (proposta, descrição, status, etc.).",
  nonconformities: {
    pageSubtitle:
      "Cadastro operacional de não conformidades no contexto LMP: material, fornecedor, quantidades, status e vínculo opcional com OV/produtos.",
    newButton:
      "Abre o formulário para registrar uma nova não conformidade. Requer permissão de escrita.",
    filters: {
      status:
        "Filtra pelo andamento da NC: Aberta, Em andamento ou Concluída. Vazio = todas.",
      branch:
        "Filial TOTVS associada ao registro (01 ou 02). Vazio = todas as filiais.",
      saleNumber:
        "Filtra pelo número da ordem de venda (OV/proposta), quando a NC estiver amarrada a uma LMP.",
      material:
        "Código do material/item informado na NC (busca parcial).",
      product:
        "Código de produto Protheus vinculado à NC (tabela de produtos).",
      dateStart:
        "Início do intervalo pela data/hora de registro da NC.",
      dateEnd:
        "Fim do intervalo pela data/hora de registro da NC.",
    },
    table: {
      section:
        "Lista paginada de não conformidades com os filtros aplicados. Use Editar/Excluir nas ações quando tiver permissão.",
      search:
        "Busca local nos registros já carregados na página (texto das colunas visíveis).",
      registeredAt: "Data e hora em que a não conformidade foi registrada.",
      saleNumber: "OV/proposta vinculada, quando informada.",
      material: "Código do material/item da ocorrência.",
      supplier: "Nome do fornecedor relacionado à NC.",
      purchaseOrder: "Número da ordem de compra (OC).",
      invoice: "Número da nota fiscal (NF).",
      qtyReceived: "Quantidade recebida no recebimento/inspeção.",
      qtyAccepted: "Quantidade aceita após análise.",
      qtyRejected: "Quantidade reprovada / não conforme.",
      status: "Andamento da NC: Aberta, Em andamento ou Concluída.",
      actions: "Editar o registro ou excluí-lo definitivamente.",
    },
    form: {
      sectionIdentification:
        "Quando e em que contexto a NC foi registrada (data/hora, status, filial e OV opcional).",
      sectionDocument:
        "Dados do documento/material: fornecedor, OC, NF e quantidades do recebimento.",
      sectionProducts:
        "Códigos Protheus opcionais amarrados à NC (podem vir da LMP/OV).",
      sectionDescription:
        "Narrativa técnica: defeito encontrado, ações tomadas e parecer.",
      registeredAt:
        "Data e hora do registro da ocorrência. Campo obrigatório.",
      status:
        "Situação atual da NC: Aberta (nova), Em andamento (tratamento) ou Concluída.",
      branch:
        "Filial TOTVS (01/02) do contexto operacional. Opcional.",
      saleNumber:
        "Número da OV/proposta LMP para amarrar a NC. Opcional.",
      material:
        "Código do material/item envolvido na não conformidade.",
      supplier: "Fornecedor do material ou serviço relacionado.",
      purchaseOrder: "Número da ordem de compra no TOTVS/ERP.",
      invoice: "Número da nota fiscal de entrada.",
      qtyReceived: "Quantidade total recebida no lote/inspeção.",
      qtyAccepted: "Quantidade aceita após conferência.",
      qtyRejected: "Quantidade reprovada / segregada.",
      productCodes:
        "Lista de códigos de produto Protheus, separados por vírgula ou espaço.",
      defectDescription:
        "Descrição objetiva do defeito ou desvio encontrado.",
      correctiveActions:
        "Ações já tomadas ou plano de ação corretiva.",
      technicalOpinion:
        "Parecer técnico / conclusão da análise.",
    },
  },
} as const;
