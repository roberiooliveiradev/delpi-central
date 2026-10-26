/** Textos dos balões de explicação — PT de negócio, sem path técnico. */

const HOME_HELP = {
  vsOverview:
    "Início é ação e descoberta. Visão geral é o painel de KPIs do período — só aparece se você tiver acesso analítico.",
  paths:
    "Caminhos por seção liberados para o seu acesso. Busque, fixe favoritos e reabra os últimos acessos. Objetivo: chegar à ação em poucos cliques.",
  search:
    "Filtra seções e rotas do catálogo pelo nome ou palavras-chave. Também dá para buscar na barra superior (Ctrl/Cmd+K).",
  favorites:
    "Atalhos que você fixou com a estrela nos caminhos. Ficam neste navegador e só mostram áreas ainda liberadas para você.",
  recents:
    "Últimas áreas abertas neste navegador. A lista respeita as permissões atuais.",
  heroUnits:
    "Quantas filiais estão liberadas no seu escopo do Portal. Os dados operacionais respeitam esse limite.",
  heroOverview:
    "Atalho para a Visão geral (KPIs do período). Só aparece liberado se você tiver acesso analítico.",
  scopeBadge:
    "Filiais do recorte. Quem tem uso normal consulta Santa Catarina e Espírito Santo; a escolha é filtro, não permissão.",
  sections: {
    attention:
      "Entrada do Portal — busca, favoritos e caminhos, sem misturar com o painel de KPIs.",
    analytics:
      "Visão geral, negociações e indicadores do período. Não substitui o bloco Atenção do Início.",
    purchase_requests:
      "Acompanhamento global das solicitações. Unidade e período são filtros. Lista vazia significa ausência de item no recorte.",
    operations:
      "Pedidos, entregas, fornecedores, produtos, estoque físico e estoque de segurança.",
    administration:
      "Mappings, escopos e configurações do Portal — só com permissão de administrar.",
    help: "Manual do usuário: Quero→onde, FAQ e glossário do Portal Suprimentos.",
  },
} as const;

export const SP_HELP = {
  shell: {
    navHome: "Busca, favoritos e atalhos para as áreas que você pode acessar.",
    navOverview:
      "Indicadores consolidados do período e das unidades selecionadas. Itens operacionais ficam em Solicitações e Operações.",
    navMyTasks: "Fila de acompanhamento atribuída a você.",
    navPurchaseRequests:
      "Itens de solicitações de compra no período. A unidade é filtro do acompanhamento global.",
    navPurchaseOrders:
      "Pedidos de compra com saldo pendente de recebimento no recorte. Unidade e período são filtros. Entregas, fornecedores, produtos e estoques ficam no agrupamento Operações do Início.",
    navAdmin: "Mappings, escopos e configurações do Portal.",
    navHelp: "O que é o Portal, diferença para os apps antigos e o que fazer em 403.",
  },
  coexistence:
    "O Portal Suprimentos reúne as jornadas. Os apps antigos (cockpit, SC, estoque de segurança) continuam no launcher até o cutover.",
  home: HOME_HELP,
  /** Alias estável para consumidores existentes. */
  homeVsOverview: HOME_HELP.vsOverview,
  suppliers:
    "Cadastro central de fornecedores (SA2, empresa 01): busca por código, loja, razão social, fantasia ou documento. A ficha abre no modo consulta com os campos agrupados por seção; na edição, código, loja e CNPJ/CPF aparecem protegidos e a revisão mostra somente o que mudou. A URL guarda busca e filtros para compartilhar.",
  suppliersSearch:
    "Busca livre por código, loja, razão social, nome fantasia ou documento (CNPJ/CPF). A lista é paginada no servidor — resultados grandes não travam a tela.",
  suppliersBlocked:
    "Situação no cadastro do ERP: Ativo ou Bloqueado (MSBLQL). Fornecedor bloqueado não deve receber novos pedidos sem validação de Compras.",
  suppliersState:
    "Filtra pelo estado (UF) do endereço cadastrado no Protheus. A opção «Todas» lista fornecedores de qualquer UF.",
  suppliersRefresh:
    "Recarrega a lista mantendo busca e filtros atuais.",
  suppliersCreate:
    "Cadastro de novo fornecedor com três inícios: consultar por CNPJ (o campo formata o documento automaticamente e traz sugestões de dados públicos com fonte e horário de Brasília — nada é aplicado sem confirmação), buscar por razão social (em homologação) ou preencher manualmente. Todos convergem para o mesmo formulário. Se o CNPJ já tiver cadastros no Protheus, o Portal lista todos com código e loja, e «Conferir cadastro» abre a ficha em nova aba — sem bloquear nem perder o formulário. O envio ao ERP só é liberado quando a escrita estiver homologada neste ambiente; fora isso, a operação fica bloqueada com aviso claro e nada é gravado.",
  suppliersColSupplier:
    "Fornecedor com identificador completo (código + loja, 8 dígitos). Clique na linha para abrir a ficha.",
  suppliersColTaxId:
    "CNPJ/CPF do fornecedor. O campo mostra a pontuação conforme o tipo de pessoa, mas o valor é salvo e enviado só com dígitos. Não é chave única — podem existir cadastros distintos com o mesmo documento. Dados de CPF chegam mascarados (LGPD).",
  suppliersColBlocked:
    "Ativo ou Bloqueado conforme o campo de bloqueio (MSBLQL) do cadastro SA2.",
  suppliersEdit:
    "Edição governada: os campos cadastrais podem ser alterados em uma única operação — exceto código, loja, CNPJ/CPF e o código do cliente vinculado, que são protegidos. Campos com catálogo (UF, país, pagamento, natureza, conta contábil, município, transportadora, segmento, administrador, cliente, funcionário e tabela de preço) oferecem pesquisa por código ou descrição — a descrição é exibida, o código é enviado. O CEP oferece sugestão de endereço com confirmação prévia. Todas as labels têm ajuda contextual com a referência física do campo no TOTVS, inclusive nos campos protegidos e na revisão. Campos modificados ganham destaque e o contador mostra quantas alterações estão pendentes; «Indisponível na consulta» indica campo não retornado pelo ERP. O envio leva só os campos modificados (PUT parcial). Antes de gravar, a revisão mostra o antes/depois agrupado por seção; após o envio, «Conferir gravação» recarrega a ficha e compara os valores.",
  suppliersIntegrationStatus:
    "Diagnóstico técnico da integração REST de fornecedores (visível para quem administra Suprimentos): «Verificar integração» consulta em tempo real a configuração, a conectividade, a autenticação técnica e a consulta REST, além das liberações de inclusão e alteração. A verificação é somente leitura — nunca cadastra nem altera fornecedores no ERP. «Habilitada» indica que a operação está liberada para uso, não que uma gravação foi comprovada. A listagem de fornecedores é consulta SQL e pode funcionar mesmo com a REST indisponível. O widget fica no canto inferior direito: expanda para os detalhes, recolha para a barra compacta ou feche pelo «×» — ele volta pelo botão flutuante discreto.",
  suppliersEnrichment:
    "Enriquecimento cadastral: compara a ficha do Protheus com dados públicos do CNPJ na BrasilAPI — fonte externa de terceiros, somente sugestão, nunca autoridade; a fonte e a data/hora da consulta aparecem em formato amigável (horário de Brasília). «Consultar dados externos» cria uma revisão sua com as diferenças por campo; aceite apenas campos elegíveis (rejeitar é sempre permitido para pendências) e as decisões em lote exigem confirmação. «Preparar atualização» gera apenas um rascunho para conferência — nenhum dado é gravado no Protheus por esta tela. O histórico mostra suas revisões anteriores; cada uma expira em 24h.",
  overviewTemporal:
    "Cada card tem natureza temporal própria: intervalo (OTD, CPV, economia), snapshot (estoque, críticos) ou estado atual (SC pendentes). Início não substitui este painel.",
  overviewFiltersPeriod:
    "Atalhos de período (Hoje, Esta semana, Este mês, trimestre, ano, 12 meses…). Ao mudar datas manualmente, o preset vira Personalizado. O recorte fica na URL (F5/compartilhar).",
  overviewFiltersFrom: "Data inicial do recorte analítico compartilhado na URL.",
  overviewFiltersTo: "Data final do recorte analítico compartilhado na URL.",
  overviewFiltersBranch:
    "Unidades liberadas no seu escopo (Santa Catarina e/ou Espírito Santo). Vazio ou ambas = consolidado. Unidade fora do escopo é bloqueada pela API.",
  overviewGoalTriad:
    "O número do card é o realizado do escopo ativo: uma unidade, ou a união Santa Catarina + Espírito Santo quando Todas. Meta do período vem do SI (comparable_goal). Para estoque (snapshot), a meta é o nível/teto cadastrado — não há pró-rata diária nem soma de meses. Meta mês/referência é a meta cadastrada consolidada. Nota IDD é o score do SI — não é recalculada no navegador.",
  overviewDepartmentIdd:
    "IDD Suprimentos é a nota canônica do Strategic Indicators para o escopo ativo do filtro. Todas ou as duas unidades mostram só o consolidado. Uma unidade mostra só Santa Catarina ou Espírito Santo. Nota ausente não vira zero.",
  overviewOtdChart:
    "Série de OTD de pedidos de compra com ChartViewShell completo (granularidade, tipo, YoY, cores e exportação). Usa o mesmo filtro de unidade e período da Visão geral. Abra OTD para ver os velocímetros.",
  overviewCompareChart:
    "Barras valor × meta só para KPIs de intervalo que já vieram no overview — com tipo, cores e exportação; não inventa série CPV/Savings.",
  overviewChartSeriesPicker:
    "Escolha qual série deste gráfico editar — incluindo comparativos quando o overlay de ano anterior estiver ativo.",
  overviewChartSeriesAppearance:
    "Cor só da série escolhida. «Restaurar todas» limpa as cores personalizadas deste gráfico neste navegador.",
  overviewChartSeriesColor:
    "Cor desta série no gráfico. Aplica somente à série selecionada.",
  otdAnalyticsPage:
    "Pontualidade de compras com velocímetros por unidade (Santa Catarina / Espírito Santo) e evolução no tempo. Diferente da Visão geral (placar de KPIs) e de Entregas / Atrasos (recebimentos MP no período selecionado).",
  marketIntelligencePage:
    "Cotações históricas de metais e câmbio de fontes autorizadas (Banco Central — PTAX, e World Bank — Pink Sheet), com atribuição e licença exibidas na própria página. Valores em USD são nativos da fonte; BRL usa a média PTAX do mês. Meses sem câmbio aparecem como indisponíveis — nunca como zero.",
  marketIntelligenceInstrument:
    "Instrumento do catálogo licenciado: metais industriais (média mensal World Bank Pink Sheet, em USD por tonelada métrica) ou a série diária USD/BRL (PTAX). Metais e câmbio nunca são misturados na mesma série.",
  marketIntelligenceCurrency:
    "USD mostra o valor nativo da fonte. BRL converte pela média PTAX de venda do mês de referência (método versionado pela API). Quando falta câmbio no mês, o ponto fica vazio e o estado parcial é sinalizado.",
  marketIntelligenceFxKind:
    "Tipo de cotação PTAX usada na conversão e na série de câmbio: venda (padrão, referência comercial) ou compra, ambas no fechamento do dia.",
  marketIntelligencePeriod:
    "Recorte da consulta. Fica na URL junto com instrumento, moeda e granularidade — F5 e compartilhamento restauram a mesma visão.",
  marketIntelligenceSummary:
    "Cards do período: última cotação válida, média aritmética das observações válidas, variação entre a primeira e a última observação e o dólar PTAX de referência. Ausência de dado aparece como «—», nunca como zero.",
  marketIntelligenceSeries:
    "Série histórica na granularidade escolhida. Pontos sem observação ficam vazios (sem interpolação). O selo indica fonte e o banner sinaliza dados parciais ou desatualizados.",
  marketIntelligenceMonthlyTable:
    "Alternativa tabular acessível ao gráfico: média mensal, média nativa em USD, PTAX do mês, número de observações e cobertura de cada período.",
  purchaseRequests:
    "Acompanhamento global das solicitações no período. Os indicadores contam SCs, não linhas: Solicitações é o total do recorte; Aguardando pedido reúne SCs ainda sem pedido completo; Aguardando recebimento reúne SCs já encaminhadas e ainda não concluídas. Atenção só filtra a lista — não é permissão nem um fluxo novo.",
  purchaseRequestsStage:
    "Situação da SC. Pode marcar várias. Aguardando pedido = aguardando pedido e pedido parcial. Aguardando recebimento = pedido emitido, aguardando entrega e recebimento parcial. Concluídas = concluída e encerrada por resíduo. A faixa Atenção aplica esses mesmos grupos.",
  purchaseRequestsAttention:
    "Atalhos do recorte atual, sem o filtro de situação. Todos limpa a situação. Os números continuam visíveis mesmo depois de escolher um atalho.",
  purchaseRequestsTableMeta:
    "No modo Tabela: colunas visíveis e total de solicitações (SCs) do recorte filtrado, não a quantidade de linhas da página.",
  purchaseRequestsCardsMeta:
    "Total de solicitações (SCs) do recorte filtrado no modo Cards, não a quantidade de linhas da página.",
  purchaseRequestsBranch:
    "Unidade do recorte (Santa Catarina e/ou Espírito Santo). «Todas» consulta todas as unidades liberadas na sessão. Códigos técnicos ficam só na URL e na API.",
  purchaseRequestsView:
    "Tabela ou Cards usam o mesmo recorte paginado. A preferência fica neste navegador e não muda dados nem permissões.",
  purchaseRequestsSort:
    "Ordene pelo cabeçalho da tabela ou, em Cards, por «Ordenar por» + Crescente/Decrescente. Colunas: SC, item, produto, solicitante, centro de custo, abertura e situação. A URL guarda sort_by e sort_dir; F5 restaura a ordem no recorte inteiro (não só a página). Situação processa o período selecionado; acima de cerca de 10 mil SCs no recorte, pode pedir um recorte menor (período ou unidade).",
  purchaseRequestsSortDirection:
    "Alterna crescente ou decrescente na mesma coluna. Vale para Cards e compartilha sort_by/sort_dir com a tabela.",
  purchaseRequestsPeriod:
    "Período de abertura da SC — mesmos atalhos da Visão geral (Hoje, Esta semana, Este mês…). Editar datas manualmente vira Personalizado. Compartilhável pela URL via date_from/date_to (F5 restaura o recorte; o atalho é derivado das datas). O padrão é Este mês.",
  purchaseRequestsNumber: "Filtra pelo número exato da solicitação de compras.",
  purchaseRequestsProduct: "Filtra pelo código exato do produto/MP da linha.",
  purchaseRequestsRequester:
    "Filtra por solicitante do recorte autorizado. A lista mostra o nome oficial da Minha DELPI quando o usuário TOTVS tem vínculo; sem vínculo, mostra o nome do ERP. Múltipla seleção combina por ou.",
  purchaseRequestsCostCenter:
    "Filtra por centro de custo dentro do seu escopo autorizado — código e descrição. Múltipla seleção combina por ou.",
  purchaseRequestsExport:
    "Exporta para Excel o recorte filtrado inteiro, sem truncar na página. Faz parte do uso normal do Portal. CSV permanece disponível como formato legado.",
  purchaseRequestsFilters:
    "Filtros aplicam automaticamente. Texto confirma após um instante ou com Enter. Atalhos de período ficam sempre visíveis (como na Visão geral). Limpar só aparece quando há filtro além do padrão (todas as unidades liberadas e período Este mês não contam sozinhos).",
  purchaseRequestsRefresh:
    "Recarrega a lista com os mesmos filtros. O horário é da última consulta bem-sucedida nesta tela, não do TOTVS.",
  purchaseRequestsTableFontSize:
    "Ajusta o tamanho da fonte da tabela neste navegador. Vale só no modo Tabela; no modo Cards o controle não aparece. A preferência fica salva localmente e volta ao retornar à Tabela.",
  purchaseRequestsTableColumns:
    "Escolha quais colunas exibir e arraste para reordenar na Tabela. No modo Cards o menu não aparece (composição fixa dos cards). A preferência fica salva neste navegador; não altera permissões nem dados.",
  purchaseRequestsColRequester:
    "Solicitante da SC com avatar de iniciais. Quando o usuário Protheus tem vínculo ativo na Minha DELPI, exibe o nome oficial da plataforma; sem vínculo, exibe o nome/código que veio do TOTVS. A ficha da pessoa ainda não existe; o avatar não abre outra página.",
  purchaseRequestsColCc: "Centro de custo da linha no escopo liberado ao usuário.",
  purchaseRequestsColOpened: "Data de abertura da solicitação de compras.",
  purchaseRequestsColStage:
    "Situação do item. Os atalhos de Atenção usam a situação conservadora da SC inteira, não só desta linha.",
  purchaseRequestsEntityLink:
    "O número da SC abre a ficha em página própria (/purchase-requests/unidade/número). Você também pode clicar na linha ou no card.",
  purchaseRequestDetail:
    "Ficha da solicitação. O cabeçalho mostra identificação, solicitante, centros de custo, aprovação e indicadores seguros (itens visíveis, pedidos vinculados e atraso) — tudo dentro do escopo de centros de custo que você enxerga. A aprovação pode variar por item; o nome do aprovador aparece quando todos os itens visíveis têm o mesmo responsável. O atraso vem das previsões de entrega dos pedidos vinculados. Cada item traz unidade, quantidades, necessidade, aprovação, fornecedor sugerido e conta contábil; abaixo ficam pedidos vinculados, recebimentos e o acompanhamento. Use Voltar para retornar à lista com os filtros anteriores.",
  purchaseRequestDetailOrders:
    "Pedidos de compra gerados a partir dos itens visíveis da solicitação. O número do PC abre a ficha do pedido — o acesso à ficha segue suas permissões: sem permissão ou fora do universo em aberto, a ficha mostra a mensagem neutra.",
  purchaseRequestDetailReceipts:
    "Documentos de entrada (NF) registrados nos pedidos vinculados, com quantidade, valor e datas de emissão e entrada. Lista vazia significa que ainda não houve entrada para os pedidos visíveis.",
  purchaseOrders:
    "Itens de pedidos de compra com saldo pendente de recebimento no recorte selecionado. O hero mostra linhas em aberto, valor em aberto e atrasadas (o chip Atrasados não muda os totais). Não é o painel OTD de pontualidade — esse fica na analytics. Clique no PC ou na linha para abrir a ficha.",
  purchaseOrdersBranch:
    "Unidade do recorte (Santa Catarina e/ou Espírito Santo). «Todas» consulta todas as unidades liberadas na sessão. Códigos técnicos ficam só na URL e na API.",
  purchaseOrdersNumber: "Filtra pelo número do pedido de compra.",
  purchaseOrdersProduct: "Filtra por código de produto/MP da linha.",
  purchaseOrdersSupplier: "Filtra pelo código do fornecedor (A2).",
  purchaseOrdersDelivery:
    "Período de entrega prometida. «Sem filtro» = nenhuma restrição de data prometida (todos os PCs abertos do recorte). Atalhos (Hoje, Esta semana…) preenchem De/Até. Personalizado = intervalo manual que não coincide com um atalho. O chip «Atrasados» em Atenção filtra linhas com prometida anterior a hoje. F5 deriva o atalho das datas na URL (sem param de preset).",
  purchaseOrdersAttention:
    "Todos (N) e Atrasados (N) usam o resumo do servidor no mesmo recorte de filtros; alternar o chip não muda os contadores. A URL guarda late_only para compartilhar ou atualizar (F5).",
  purchaseOrdersRefresh:
    "Recarrega a lista e o resumo com os mesmos filtros. O horário é da última consulta bem-sucedida nesta tela, não do TOTVS.",
  purchaseOrdersFilters:
    "Filtros aplicam automaticamente. Texto confirma após um instante ou com Enter. Atalhos de período de entrega ficam sempre visíveis (como na Visão geral). Limpar só aparece quando há filtro além do padrão (todas as unidades liberadas não contam sozinhas).",
  purchaseOrdersView:
    "Tabela ou Cards usam o mesmo recorte paginado. A preferência fica neste navegador e não muda dados nem permissões.",
  purchaseOrdersSort:
    "Ordene pelo cabeçalho da tabela ou, em Cards, por «Ordenar por» + Crescente/Decrescente. A URL guarda sort_by e sort_dir; F5 restaura a ordem no recorte inteiro (não só a página atual).",
  purchaseOrdersSortDirection:
    "Alterna crescente ou decrescente na mesma coluna. Vale para Cards e compartilha sort_by/sort_dir com a tabela.",
  purchaseOrdersExcel:
    "Exporta para Excel o recorte filtrado inteiro, sem truncar na página. Exige o uso normal do Portal.",
  purchaseOrdersTableFontSize:
    "Ajusta o tamanho da fonte da tabela neste navegador. Vale só no modo Tabela; no modo Cards o controle não aparece. Use − / + ou restaurar o padrão. A preferência fica salva localmente e volta ao retornar à Tabela.",
  purchaseOrdersTableColumns:
    "Marque ou desmarque colunas e arraste pelo handle para reordenar na Tabela. No modo Cards o menu não aparece (composição fixa dos cards). Restaurar volta ao padrão. A preferência fica salva neste navegador; não altera permissões nem dados.",
  purchaseOrdersTableMeta:
    "No modo Tabela: colunas visíveis e total de linhas do recorte filtrado (não só a página atual).",
  purchaseOrdersCardsMeta:
    "Total de linhas do recorte filtrado no modo Cards (não só a página atual). Fonte e Colunas são preferências só da Tabela.",
  purchaseOrdersColSupplier:
    "Fornecedor da linha com avatar de iniciais, no mesmo padrão visual do Portal Comercial. A ficha do fornecedor ainda não existe; o avatar não abre outra página.",
  purchaseOrdersColOpenQty: "Quantidade ainda em aberto (saldo a receber) nesta linha.",
  purchaseOrdersColDelivery: "Data prometida de entrega do item.",
  purchaseOrdersColStatus: "Situação em relação à data prometida: atrasado, no prazo ou sem data.",
  purchaseOrdersColOpenValue: "Valor em aberto da linha (saldo × preço).",
  purchaseOrdersEntityLink:
    "O número do PC abre a ficha do pedido. Você também pode clicar na linha.",
  purchaseOrderDetail:
    "Ficha somente leitura do pedido em aberto: cabeçalho com filial, fornecedor e comprador (quando todos os itens têm o mesmo responsável) e indicadores de itens em aberto e atraso. Cada item traz quantidades, preços, data prometida, recebimentos e a SC de origem — a SC abre a ficha da solicitação. O indicador de atraso vem da situação de cada item; não exibe dias porque o contrato não traz esse número. Copie o endereço da página para compartilhar; atualizar restaura a mesma ficha. Pedidos encerrados não aparecem: «não localizado» significa apenas fora do universo em aberto consultável.",
  purchaseOrderDetailItems:
    "Cada item traz fornecedor, quantidades, entrega prometida e a solicitação de origem — clicável para abrir a ficha da SC. Um mesmo pedido pode ter itens de solicitações e fornecedores diferentes.",
  purchaseOrderDetailReceipts:
    "Recebimentos do item, com nota, quantidade, datas de emissão e entrada. Se a lista estiver vazia, ainda não há documento de entrada para aquela linha.",
  deliveries:
    "Linhas de recebimento de matéria-prima (MP) classificadas por pontualidade. Em atraso = recebimento depois da data prometida; No prazo = no compromisso ou antes. O período usa a data de digitação/entrada do recebimento — não a data prometida nem a emissão do PC. Não é a lista de Pedidos de compra (saldo aberto) nem o OTD analítico.",
  deliveriesBranch:
    "Unidade do recorte (Santa Catarina e/ou Espírito Santo). «Todas» omite o parâmetro branch na URL; o Portal consulta o consolidado autorizado. Códigos técnicos ficam só na URL e na API.",
  deliveriesPeriod:
    "O período considera a data de digitação/entrada do recebimento. Não filtra pela data prometida nem pela emissão do pedido. Atalhos preenchem De/Até; Personalizado = intervalo manual. A URL guarda start_date e end_date (F5 restaura o recorte).",
  deliveriesStatus:
    "Situação de pontualidade do recebimento: Em atraso ou No prazo. O valor vem do servidor; o Portal não recalcula atraso a partir dos dias.",
  deliveriesFilters:
    "Filtros aplicam automaticamente. A URL guarda unidade, situação, período, página e ordenação para compartilhar ou atualizar (F5). Limpar volta ao padrão (Todas, Em atraso, mês corrente). Não há clique no pedido nesta tela.",
  deliveriesRefresh:
    "Recarrega a lista e o resumo com os mesmos filtros. O horário é da última consulta bem-sucedida nesta tela.",
  deliveriesTableMeta:
    "Colunas visíveis e total de linhas do recorte filtrado (não só a página atual). Pedido aparece como texto — não abre ficha nesta página.",
  inventory:
    "Posição física atual do estoque no Protheus, por produto, unidade e armazém. Inclui saldos positivos, zerados e negativos. Não é estoque de segurança nem saldo disponível.",
  inventoryBranch:
    "Unidade do recorte (Santa Catarina e/ou Espírito Santo). «Todas» = exatamente essas duas unidades liberadas no Portal — não todas as filiais do ERP. Códigos técnicos ficam só na URL e na API.",
  inventoryWarehouse:
    "Armazém do recorte. «Todos» preserva todos os códigos retornados, inclusive sem descrição. A lista de opções vem do servidor; o Portal não usa lista fixa de armazéns.",
  inventoryPhysicalBalance:
    "Saldo físico é a quantidade atual registrada no estoque. Não é saldo disponível — a tela não desconta reservas, empenhos nem outras regras.",
  inventoryStockValue:
    "Valor operacional da posição (saldo físico × custo médio unitário do contrato). O Hero mostra o valor consolidado do recorte; a coluna Valor do saldo é por linha.",
  inventoryFilters:
    "Filtros aplicam automaticamente. A URL guarda unidade, armazém, página e ordenação (F5 restaura). Limpar volta a Todas as unidades e Todos os armazéns.",
  inventoryRefresh:
    "Recarrega o resumo e a lista com os mesmos filtros. O horário é da última consulta bem-sucedida nesta tela.",
  inventoryTableMeta:
    "Colunas visíveis e total de posições do recorte filtrado (não só a página atual). Produto não abre ficha nesta página.",
  safetyStock:
    "Materiais com estoque de segurança parametrizado no Protheus. Classificação, saldos e déficit são calculados pelo servidor — o Portal apenas exibe. Saldo disponível considera os armazéns 01, 98 e 99. Os cartões de indicadores também filtram a lista: clique em um para ver só aquele recorte (equivale ao filtro Status, combinado com a filial e os demais filtros).",
  safetyStockBranch:
    "Filial do recorte (Santa Catarina, Espírito Santo ou Todas). «Todas as filiais» é uma única consulta consolidada — não soma manual de duas buscas. Filial é filtro de dados, não permissão.",
  safetyStockStatus:
    "Situação do material em relação ao estoque de segurança, classificada pelo servidor: sem estoque de segurança, abaixo, no nível ou acima.",
  safetyStockProductGroup:
    "Grupo de produto do recorte. A lista de opções vem do servidor conforme o universo da filial selecionada.",
  safetyStockUnit:
    "Unidade de medida do material. Filtrar por UM evita misturar quantidades de grandezas diferentes.",
  safetyStockSearch:
    "Busca por código ou descrição do produto. Aplica automaticamente após digitar (debounce) ou com Enter.",
  safetyStockIncludeBlocked:
    "Quando ligado, materiais bloqueados no Protheus também entram no recorte — útil para avaliar o estoque de segurança de itens inativos.",
  safetyStockIncludeWithoutSafetyStock:
    "Quando ligado (padrão), inclui materiais sem estoque de segurança parametrizado — eles aparecem com status «Sem estoque de segurança». Desligar restringe a quem tem estoque de segurança definido.",
  safetyStockFilters:
    "Filtros aplicam automaticamente. A URL guarda filial, status, grupo, UM, busca, toggles, página e ordenação (F5 restaura). Limpar volta a Todas as filiais sem demais filtros.",
  safetyStockRefresh:
    "Recarrega filtros, resumo e lista com o mesmo recorte. O horário é da última consulta bem-sucedida nesta tela.",
  safetyStockSafetyStock:
    "Quantidade de estoque de segurança parametrizada no Protheus para o produto naquela filial.",
  safetyStockPrimaryStock:
    "Saldo físico no armazém principal da filial. Não é saldo disponível — não desconta empenhos nem reservas.",
  safetyStockWorkInProcess:
    "Saldo registrado nos armazéns de processo (50, 98 e 99).",
  safetyStockDeficit:
    "Déficit = estoque de segurança menos saldo disponível (armazéns 01+98+99), nunca negativo. Calculado pelo servidor.",
  safetyStockColProduct:
    "Código de identificação do material no Protheus.",
  safetyStockColDescription:
    "Descrição cadastrada para o material.",
  safetyStockColBranch:
    "Filial relacionada ao registro. Na consulta consolidada («Todas as Filiais»), a linha agrega as filiais operacionais — ao abrir o detalhe, você escolhe a filial (Santa Catarina ou Espírito Santo).",
  safetyStockColType:
    "Classificação do tipo de material utilizada no cadastro do Protheus.",
  safetyStockColGroup:
    "Grupo ao qual o material pertence no cadastro.",
  safetyStockColUnit:
    "Unidade de medida utilizada para representar as quantidades do material.",
  safetyStockColActions:
    "Abre a página de detalhe do material na filial correspondente. Na visão «Todas as Filiais», você escolhe a filial antes de abrir.",
  safetyStockTableMeta:
    "Colunas visíveis e total de materiais do recorte filtrado (não só a página atual). Clique na linha ou em «Ver detalhes» para abrir a página de detalhe do material na filial.",
  safetyStockDetail:
    "Página de detalhe do material nesta filial: identificação, saldos, cobertura do déficit, pedidos/solicitações/empenhos em aberto, projeção de estoque, consumo e fornecedores vinculados. Tudo calculado pelo servidor — o Portal não recalcula.",
  safetyStockDetailCoverage:
    "Cobertura do déficit pelos pedidos de compra elegíveis (armazéns 01/98/99 e unidade compatível). «Falta comprar» é o restante calculado pelo servidor.",
  safetyStockDetailProjection:
    "Extrato cronológico projetado pelo servidor: saldo inicial, entradas de pedidos elegíveis e saídas de empenhos elegíveis. Ruptura = primeiro saldo projetado negativo.",
  safetyStockDetailSuppliers:
    "Fornecedores vinculados ao material com dados da última compra. Identidade do fornecedor é código + loja.",
  userProfile:
    "Preferências do Portal Suprimentos (filial padrão e densidade) e atalhos por capability. O avatar na TopBar abre o perfil deste Portal; identidade global (foto, cargo, contatos) edita-se no Meu Perfil Minha DELPI (/profile) pelo menu do nome.",
  userProfilePrefs:
    "Filial padrão e densidade de tabelas valem só neste Portal. Só você edita o próprio perfil; administradores podem ler outros usuários.",
  forbiddenUnit:
    "Você não tem permissão para este módulo. Peça o uso normal do Portal ao administrador — aliases antigos não abrem o app.",
} as const;

/** Hints do inspector Séries (COLOR_ONLY nos gráficos da Visão geral). */
export const SP_CHART_SERIES_HINTS = {
  series: SP_HELP.overviewChartSeriesPicker,
  appearance: SP_HELP.overviewChartSeriesAppearance,
  color: SP_HELP.overviewChartSeriesColor,
} as const;
