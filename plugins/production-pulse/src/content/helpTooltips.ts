/**
 * Catálogo central de helps — Pulso de Produção (hover no rótulo / SectionHintLabel).
 * Copiar para `plugins/production-pulse/src/content/helpTooltips.ts` no scaffold E5.S1.
 */
export const PP_HELP = {
  apiErrors: {
    apiUnavailable: "API Pulso de Produção indisponível. Tente novamente em instantes.",
  },

  shell: {
    heroTitle:
      "Monitoramento de dispositivos IoT na filial: contadores, sensores de rotação, temperatura e demais métricas.",
    heroFilial: "Filial operacional dos dispositivos e sensores cadastrados.",
    pollAll:
      "Solicita leitura imediata em todos os dispositivos ativos da filial. Requer permissão de gestão.",
    breadcrumbRoot: "Pulso de Produção",
    backToPanel: "Volta ao painel principal de dispositivos.",
    modeOperator: "Abre a visão simplificada para tablet no chão de fábrica.",
  },

  panel: {
    kpiTotal:
      "Quantidade de dispositivos IoT cadastrados na filial, incluindo rascunhos sem amarração.",
    kpiOnline:
      "Dispositivos que responderam à última leitura dentro do intervalo esperado (online).",
    kpiOffline:
      "Dispositivos sem resposta HTTP no tempo limite — verifique rede, energia ou IP.",
    kpiWithoutBinding:
      "Cadastros incompletos: falta informar posto, máquina, equipamento ou área de instalação.",
    kpiCounterDeltaDay:
      "Soma dos incrementos de golpe (delta) de todos os contadores amarrados na filial, desde a meia-noite local.",
    kpiCounterDeltaShift:
      "Soma dos incrementos de golpe no turno operacional atual (06–14, 14–22 ou 22–06).",
    filterAnchorType:
      "Filtra por tipo de amarração: posto PCP, máquina, equipamento, área ou avulso.",
    filterRole:
      "Filtra pelo papel do device: contador de golpes, sensor de processo ou telemetria.",
    filterStatus: "Online, offline, desativado ou sem amarração.",
    filterSearch:
      "Busca por nome do device, rótulo do objeto (placement) ou endereço IP.",
    filterGroupBy:
      "Na vista agrupada, define se os devices aparecem por posto, máquina, equipamento ou área.",
    viewTable: "Tabela com colunas — ideal para comparar muitos devices de uma vez.",
    viewCards: "Cards com nome, objeto, métrica e ações — mais legível em telas menores.",
    viewGrouped: "Seções colapsáveis agrupadas pelo objeto operacional escolhido.",
    colName: "Nome do dispositivo IoT (ESP ou gateway) — identificação técnica na rede.",
    colPlacement:
      "Onde o sensor está instalado: posto, máquina, equipamento ou área. Vem da amarração.",
    colRole:
      "Função operacional derivada do driver: contador, sensor ou telemetria.",
    colMetric:
      "Última leitura em cache — golpes, rotação, temperatura etc., conforme o driver.",
    colStatus: "Online se houve poll recente com sucesso; offline se timeout ou erro.",
    colLastSeen: "Momento da última comunicação bem-sucedida com o hardware.",
    rowPoll: "Lê o device agora e atualiza a métrica exibida.",
    rowPollAction: "Atualizar",
    cardOpenDetail: "Ver detalhe",
    pollNoticeTitle: "Dispositivo não respondeu",
    pollNoticeClose: "Fechar",
    retryLoad: "Tentar novamente",
    clearFilters: "Limpar filtros",
    rowReset:
      "Zera o contador físico (somente devices contador). Operação auditada.",
    emptyFilial:
      "Nenhum device nesta filial. Cadastre sensores ou contadores para começar.",
    emptyFilters:
      "Nenhum resultado com os filtros atuais. Limpe os filtros ou altere a busca.",
  },

  form: {
    sectionDevice:
      "Hardware na rede: endereço IP, driver (protocolo) e intervalo de leitura automática.",
    sectionPlacement:
      "Onde o sensor está fisicamente: posto de produção, máquina, equipamento medido ou área.",
    sectionTotvs:
      "Opcional. Vincula o device a um centro de trabalho TOTVS para contexto PCP — não obrigatório para ventiladores, motores auxiliares etc.",
    name:
      "Nome técnico do device na rede (ex.: ESP ventilador A). Diferente do equipamento medido.",
    filial: "Filial onde o IP do device é único. Não pode ser alterada após criar.",
    ip:
      "Endereço IPv4 fixo do hardware na rede industrial. Deve ser alcançável pela API.",
    controllerCode:
      "Identidade do chip no firmware (página do ESP /api/status). «Testar conexão» preenche automaticamente quando o device responde.",
    driver:
      "Protocolo/firmware instalado no device. Define quais métricas são lidas e se há comandos (+/−/zerar).",
    driverPreview:
      "Resumo das métricas e comandos suportados pelo driver selecionado.",
    pollInterval:
      "Intervalo em milissegundos entre leituras automáticas (mín. 1, máx. 300000). Default 30000.",
    enabled:
      "Desligado — para de pollar e some do hub operador; histórico é preservado.",
    testConnection:
      "Testa comunicação HTTP com o device sem gravar histórico. No cadastro novo usa test-probe (IP + driver); na edição, test no device salvo.",
    testConnectionAction: "Testar conexão",
    testConnectionLoading: "Testando…",
    anchorType:
      "Tipo de objeto onde o sensor está: posto PCP (CT), máquina, equipamento, área ou avulso.",
    anchorWorkCenter:
      "Obrigatório quando o tipo é Posto PCP. Centro de trabalho cadastrado no TOTVS.",
    anchorMachine:
      "Nome da máquina monitorada (torno, prensa, compressor). Obrigatório para tipo Máquina.",
    anchorEquipment:
      "Equipamento medido (ventilador, motor, bomba). Obrigatório para tipo Equipamento.",
    anchorArea:
      "Zona ou linha (Sala HVAC, Subestação). Obrigatório para tipo Área.",
    anchorStandalone:
      "Device avulso — usa o nome do device como referência operacional.",
    workCenterOptional:
      "Atalho TOTVS. Opcional para máquina/equipamento; útil para cruzar com fila PCP.",
    resourceOptional:
      "Recurso TOTVS (quando disponível). Enriquece o vínculo operacional.",
    toolOptional: "Ferramenta TOTVS da alocação, quando aplicável.",
    notes: "Observações livres sobre instalação, cabeamento ou calibração.",
    cancel: "Descarta alterações não salvas.",
    save: "Grava device e amarração. Device incompleto fica como rascunho.",
  },

  detail: {
    tabOverview: "Status ao vivo, amarração vigente e métricas atuais do device.",
    tabHistory: "Gráfico e tabela de leituras ao longo do tempo.",
    tabCommands: "Auditoria de comandos enviados ao hardware (zerar, +/−).",
    liveMetrics:
      "Valores lidos na última comunicação. A tela atualiza sozinha no ritmo do intervalo de poll do dispositivo.",
    bindingCard:
      "Objeto operacional onde o sensor está instalado. CT TOTVS aparece aqui quando vinculado.",
    chartDelta:
      "Variação entre leituras consecutivas — relevante para contadores de golpe.",
    chartSeries:
      "Evolução temporal de cada métrica (rpm, °C, golpes) conforme o driver.",
    readingsTable: "Histórico paginado de polls e comandos gravados no banco.",
    commandsTable:
      "Quem executou cada comando, quando e se o hardware respondeu com sucesso.",
    pollNow: "Força leitura imediata e grava no histórico.",
    pollNowAction: "Atualizar agora",
    pollNowLoading: "Atualizando…",
    resetCounter:
      "Zera o contador no ESP. Use com cuidado — ação registrada em auditoria.",
    deactivate:
      "Desativa o device (soft delete). Para polling; não apaga histórico.",
    delta:
      "Diferença em relação à leitura anterior — só para métricas monotônicas (golpes).",
    counterHardwareReset:
      "O contador físico caiu (ex.: device desligado). A plataforma restaura o último valor (POST /api/definir) ou mantém continuidade lógica até o firmware aceitar set.",
    coverageIncomplete:
      "Pode haver lacunas se o device ficou offline ou o poll falhou.",
  },

  modals: {
    resetTitle: "Confirma zerar o contador físico deste device?",
    resetBody:
      "O valor no hardware volta a zero. A operação fica registrada com seu usuário.",
    clearOperatorTitle: "Zerar contador para 0?",
    clearOperatorBody: "Confirme apenas se a contagem atual estiver incorreta.",
    testOk: "Conexão OK. Métricas retornadas pelo driver.",
    testFail:
      "Não foi possível alcançar o device. Verifique IP, cabo, Wi‑Fi ou firewall.",
    testTitle: "Testar conexão",
    testLoading: "Testando comunicação com o device…",
    testLatencyPrefix: "Latência",
    testControllerCodePrefix: "Código do controlador",
    testClose: "Fechar",
    deactivateTitle: "Desativar este dispositivo?",
    deactivateBody:
      "Para leituras automáticas. O cadastro e o histórico permanecem consultáveis.",
  },

  operator: {
    hubTitle:
      "Escolha onde vai trabalhar: posto, máquina ou equipamento com sensores cadastrados.",
    hubFilterAll: "Mostra todos os locais com devices elegíveis para operador.",
    hubFilterWorkCenter: "Somente postos vinculados a centro de trabalho PCP.",
    hubFilterMachine: "Somente máquinas com um ou mais sensores.",
    hubFilterEquipment: "Somente equipamentos (ventilador, motor, bomba…).",
    hubSearch:
      "Busca por nome do posto, máquina, equipamento ou código CT.",
    hubSearchClear: "Limpar busca",
    hubSearchAria: "Busca por posto, máquina ou equipamento",
    hubCardMeta:
      "Quantidade de sensores/contadores no local e quantos estão online.",
    pickerTitle: "Este local tem mais de um device — escolha qual usar.",
    pickerBadgeCounter: "Contador de golpes — permite +/− e zerar.",
    pickerBadgeSensor: "Sensor de processo — somente leitura (rpm, °C…).",
    statusBar:
      "Local de instalação, status de comunicação e há quanto tempo foi a última leitura.",
    counterValue: "Total de golpes registrado pelo hardware neste momento.",
    counterIncrement:
      "Adiciona um golpe manualmente — para correção ou acionamento sem sensor.",
    counterDecrement:
      "Remove um golpe — use só para corrigir contagem errada.",
    counterClear:
      "Zera o contador. Pedirá confirmação antes de enviar ao device.",
    gaugeValue: "Leitura atual do sensor — atualiza automaticamente a cada poucos segundos.",
    gaugeThresholdWarn:
      "Valor acima do limite de atenção definido no driver — verifique o processo.",
    gaugeThresholdDanger:
      "Valor acima do limite crítico — risco operacional; ação imediata recomendada.",
    gaugeRefresh: "Força nova leitura sem esperar o ciclo automático.",
    changePlacement: "Volta à lista de locais para escolher outro posto ou equipamento.",
    offlineBanner:
      "Sem comunicação com o device. Comandos ficam desabilitados até reconectar.",
    adminLink: "Abre o painel administrativo completo (se você tiver permissão).",
    brandEyebrowPrefix: "PULSO",
  },

  badges: {
    anchorWorkCenter: "Posto de produção com centro de trabalho TOTVS.",
    anchorMachine: "Máquina ou célula industrial.",
    anchorEquipment: "Equipamento monitorado (ventilador, motor, bomba).",
    anchorArea: "Área ou zona da planta.",
    anchorStandalone: "Device sem local fixo cadastrado.",
    roleCounter: "Conta golpes ou ciclos de produção.",
    roleGauge: "Mede grandezas contínuas: rotação, temperatura, pressão.",
    roleTelemetry: "Múltiplas métricas ou gateway de sensores.",
    statusOnline: "Device respondeu recentemente.",
    statusOffline: "Sem resposta na última tentativa de leitura.",
    statusNoBinding: "Cadastro incompleto — falta amarração.",
    statusDisabled: "Device desativado pelo administrador.",
  },
} as const;

export type PpHelpKey = typeof PP_HELP;

/** Resolve chave aninhada — ex.: getHelp("panel.kpiOnline") */
export function getPpHelp(path: string): string | undefined {
  const parts = path.split(".");
  let cur: unknown = PP_HELP;
  for (const p of parts) {
    if (cur == null || typeof cur !== "object" || !(p in cur)) return undefined;
    cur = (cur as Record<string, unknown>)[p];
  }
  return typeof cur === "string" ? cur : undefined;
}
