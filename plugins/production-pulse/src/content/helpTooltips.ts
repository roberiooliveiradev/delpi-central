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
    topBar:
      "Navega entre Painel, Hub OTA e modo operador (quando permitido). Em telas estreitas vira menu ☰.",
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
      "Identidade do chip no firmware (página do ESP /api/status). «Testar conexão» preenche automaticamente quando o device responde. Na LAN, o mDNS usa este código (ex.: esp-00a1b2c3.local).",
    wifiSsid:
      "Nome da rede Wi-Fi gravada no chip (EEPROM). Enviado ao dispositivo no Salvar.",
    wifiPassword:
      "Senha da rede Wi-Fi. Write-only: em branco = não altera a senha já gravada no chip. Nunca é armazenada no Postgres.",
    debounceMs:
      "Tempo de debounce dos botões no ESP (ms). Em branco no cadastro = default do firmware.",
    apiToken:
      "Segredo compartilhado plataforma↔chip (header X-Device-Token). Protege status, config e comandos; só a contagem (GET /api/contador) fica pública. Em branco = não altera o token já gravado.",
    apiTokenSetHint:
      "Já existe token neste cadastro. Deixe em branco para manter, ou informe um novo / use «Gerar token».",
    generateApiTokenAction: "Gerar token",
    deviceConfigPushFailed:
      "Cadastro salvo, mas não foi possível enviar a configuração ao dispositivo. Verifique IP, energia e token.",
    deviceConfigPushOk: "Configuração enviada ao dispositivo.",
    deviceConfigPushSkipped: "Cadastro salvo. Nenhuma configuração de chip para enviar.",
    firmwareSourceDeprecated:
      "Sketch legado no cadastro do device — substituído pelo catálogo de versões. Use a aba Firmware para ver a resolução exact-version.",
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
    tabFirmware:
      "Versão OTA instalada/alvo, última publicada e sketch resolvido por versão exacta (nunca latest como instalado).",
    firmwareEmpty: "Nenhum sketch disponível para esta versão.",
    firmwareInstalledSource:
      "Sketch da versão exata instalada no cadastro — resolvido no catálogo de firmwares.",
    firmwareTargetSource: "Sketch da versão alvo da atualização OTA em andamento.",
    firmwareLegacySource:
      "Texto legado gravado no device antes do catálogo — fallback explícito, não substitui versão instalada.",
    firmwareLegacyBadge: "Sketch legado do dispositivo",
    firmwareInstalledMissingVersion:
      "Informe installedFirmwareVersion no cadastro para resolver o sketch instalado.",
    firmwareInstalledNotInCatalog: "Versão instalada não existe no catálogo de firmwares.",
    firmwareInstalledNoSource: "Versão instalada existe, mas não tem sketch cadastrado.",
    firmwareTargetNoSource: "Versão alvo existe, mas não tem sketch cadastrado.",
    firmwareSourcesFailed: "Não foi possível carregar os sketches deste dispositivo.",
    firmwareCopy: "Copiar código",
    firmwareCopied: "Copiado",
    firmwareCopyFailed: "Não foi possível copiar. Selecione o texto e copie manualmente.",
    liveMetrics:
      "Valores lidos na última comunicação. A tela atualiza sozinha no ritmo do intervalo de poll do dispositivo.",
    chipHealth:
      "Telemetria do chip via GET /api/status (versão, uptime, RSSI, heap). Atualiza ao usar «Atualizar agora».",
    chipHealthTitle: "Saúde do chip",
    chipHealthVersion: "Firmware",
    chipHealthUptime: "Uptime",
    chipHealthRssi: "Wi-Fi RSSI",
    chipHealthHeap: "Heap livre",
    chipHealthWifi: "Wi-Fi",
    chipHealthWifiOnline: "Conectado",
    chipHealthWifiOffline: "Desconectado",
    bindingCard:
      "Objeto operacional onde o sensor está instalado. CT TOTVS aparece aqui quando vinculado.",
    chartDelta:
      "Variação entre leituras consecutivas — relevante para contadores de golpe.",
    chartSeries:
      "Evolução temporal de cada métrica (rpm, °C, golpes) conforme o driver. O eixo X adapta a granularidade ao intervalo (segundos, minutos, horas).",
    historyRangePresets:
      "Atalhos de período (1 min → 12 meses, este mês). Acima de 7 dias o gráfico usa agregação horária; acima de 90 dias, diária. A tabela continua com leituras raw paginadas. O histórico só recarrega em «Atualizar agora»/comando — não a cada tick live. Livre usa data/hora manual.",
    readingsTable:
      "Histórico paginado de polls e comandos gravados no banco (resolução raw). Raw antigo pode ser purgado pela retenção; o gráfico longo usa rollups.",
    commandsTable:
      "Quem executou cada comando, quando e se o hardware respondeu com sucesso.",
    pollNow: "Força leitura imediata e grava no histórico.",
    pollNowAction: "Atualizar agora",
    pollNowLoading: "Atualizando…",
    editDevice: "Abre o formulário para alterar IP, driver, Wi‑Fi, token e amarração.",
    resetCounter:
      "Zera o contador no ESP. Use com cuidado — ação registrada em auditoria.",
    factoryReset:
      "Restaura Wi-Fi/token/debounce no chip (EEPROM) e reinicia. Histórico no banco não é apagado.",
    factoryResetAction: "Factory reset",
    deactivate:
      "Desativa o device (soft delete). Para polling; não apaga histórico.",
    delta:
      "Diferença em relação à leitura anterior — só para métricas monotônicas (golpes).",
    counterHardwareReset:
      "Queda no poll sem comando recente do pad: a plataforma restaura o valor persistido (SET no chip ou offset lógico). Diminuir/Limpar via API não disparam restore.",
    coverageIncomplete:
      "Pode haver lacunas se o device ficou offline ou o poll falhou.",
  },

  ota: {
    openCatalog: "Catálogo de firmwares publicados para atualização OTA.",
    openJobs: "Hub de amarração — disparo imediato, agendamento e acompanhamento OTA.",
    openLinks: "Hub: amarrar IoTs, disparar OTA e acompanhar atualizações.",
    catalogHero:
      "Versões por família: sketch (.ino) e bin (.bin) na mesma release. Rascunho permite source antes do bin.",
    createVersionForm:
      "Crie rascunho (source ± bin) ou publique direto com .bin. Chave e versão são imutáveis após criar.",
    publishForm: "Envia o artefato .bin e metadados. Requer permissão de gestão.",
    detailMetadata: "Identidade imutável da versão (família, versão, driver) e timestamps de lifecycle.",
    detailSource:
      "Snapshot do sketch (.ino) desta versão. Rascunho: editável; publicado: somente leitura.",
    detailArtifact: "Binário OTA (.bin) usado pelo ESP. Publicar exige artefato anexado.",
    sourceFile: "Importe um arquivo .ino — o texto entra no snapshot da versão (não é flashável via OTA).",
    sourceTextarea: "Cole ou edite o sketch. Limite ~256 KiB por versão.",
    sourceFileReadFailed: "Não foi possível ler o arquivo .ino selecionado.",
    sourceEmpty: "Nenhum sketch cadastrado nesta versão.",
    fileOptionalDraft: "Opcional no rascunho — obrigatório para publicar.",
    publishRequiresBin: "Publicar exige anexar o artefato .bin.",
    publishVersion: "Torna a versão elegível para OTA. Source e bin ficam imutáveis.",
    publishConfirmTitle: "Publicar esta versão?",
    publishConfirmBody:
      "Após publicar, sketch e binário não podem ser alterados. Corrigir exige nova versão.",
    editMetadata: "Edita nome exibido e notas — permitido em rascunho e publicado (até arquivar).",
    artifactEmptyDraft: "Anexe o .bin antes de publicar.",
    artifactImmutable: "Artefato publicado não pode ser substituído.",
    statusPublished: "Publicado",
    statusArchived: "Arquivado",
    firmwareKey: "Identificador da família (EN). Devices usam o mesmo valor para OTA.",
    driverKey: "Driver do registry compatível com os IoTs desta família (select).",
    driverKeyEmpty: "Lista de drivers indisponível — digite a chave EN do driver.",
    version: "Versão semântica do binário (ex.: 1.3.0).",
    displayName: "Nome amigável na UI (pode ser em português).",
    file: "Anexe o .bin gerado ao compilar o sketch (ex.: Teste.ino). O fonte .ino não é o artefato OTA. O sha256 é calculado no servidor.",
    releaseNotes: "Notas opcionais da versão para operadores/admin.",
    catalogList: "Versões disponíveis por família de firmware. Arquivar remove a versão de novos disparos.",
    catalogEmpty: "Nenhuma versão publicada ainda.",
    archiveFirmware: "Arquiva a versão: permanece no histórico e não entra em novas campanhas OTA.",
    archiveConfirmTitle: "Arquivar esta versão de firmware?",
    archiveConfirmBody:
      "A versão deixa de ser elegível para novos disparos OTA. O histórico e jobs antigos permanecem.",
    cancelConfirmTitle: "Cancelar esta atualização OTA?",
    cancelConfirmBody: "Targets ainda não concluídos deixam de baixar o artefato.",
    jobsHero: "Dispare atualização agora ou agende. O ESP baixa quando autorizado.",
    jobCreate: "Escolha o firmware, o disparo (agora/agendar) e o escopo (filial ou device).",
    jobFirmware: "Versão publicada (não arquivada) que será enviada aos IoTs elegíveis.",
    jobTrigger: "Agora autoriza na hora; Agendar espera a data/hora.",
    jobScheduledAt: "Data e hora local em que a atualização autoriza os targets.",
    jobScope: "Filial (todos elegíveis amarrados) ou apenas o IoT selecionado no canvas.",
    jobScopeDevice: "Device alvo quando o escopo não é a filial inteira.",
    jobsList: "Atualizações recentes da filial e status (lifecycle + outcome).",
    jobsEmpty: "Nenhuma atualização criada.",
    targetsList: "Status por dispositivo na atualização selecionada.",
    deviceVersionCard:
      "Versão reportada pelo chip e alvo da última atualização. Sketch .ino é independente do OTA.",
    runningVersion: "Versão que o chip está executando agora (telemetria live ou última reportada).",
    downloadProgress: "Percentual real do download do .bin reportado pelo ESP durante a OTA.",
    awaitingDevice: "Aguardando chip",
    awaitingChip:
      "Autorizado ou pendente: aguardando o chip buscar o artefato — sem percentual fictício.",
    progressPhases: "Etapas da atualização: autorizado, baixando, aplicando e concluído.",
    noPublishedFirmware: "Não há firmware publicado para esta família.",
    deviceJobCreated: "Atualização criada. Acompanhe o progresso; o chip aplica no próximo check OTA.",
    deviceJobFailed: "Não foi possível criar a atualização OTA.",
    status: {
      pending: "Pendente",
      authorized: "Autorizado",
      downloading: "Baixando",
      applying: "Aplicando",
      updated: "Atualizado",
      failed: "Falhou",
      skipped: "Ignorado",
      cancelled: "Cancelado",
      draft: "Rascunho",
      scheduled: "Agendado",
      running: "Em andamento",
      completed: "Concluído",
    },
    operation: {
      idle: "Nenhuma atualização em andamento.",
      pending: "Aguardando autorização da campanha.",
      authorized: "Autorizado — o chip vai buscar o artefato no próximo check.",
      downloading: "Baixando o firmware para a flash do chip.",
      applying: "Aplicando o binário e reiniciando o controlador.",
      updated: "Atualização concluída com sucesso.",
      failed: "A atualização falhou — verifique o código de erro e a rede.",
    },
  },

  otaLinks: {
    hero: "Admin mapa: amarre cada IoT a um firmware, dispare atualização e acompanhe o progresso no canvas.",
    branch: "Filial dos IoTs exibidos no canvas e nas atualizações.",
    refresh: "Recarrega firmwares, devices e jobs; soft reload de jobs não bloqueia a tela.",
    canvas: "Arraste do firmware (esquerda) para o IoT. Clique no nó para resumo; ⋯ para ações.",
    connect: "Cria ou substitui o vínculo (1 IoT = 1 firmware).",
    disconnect: "Use Desvincular no menu ⋯ ou Backspace/Delete na seta sólida. A tracejada (driver) permanece.",
    inherited:
      "Seta tracejada: IoT e firmware compartilham o mesmo driver — indicação automática, não removível por desvínculo.",
    oneFirmwarePerDevice: "Cada IoT só pode ter um firmware; conectar outro substitui o anterior.",
    afterPublish: "Após publicar, amarre os IoTs no mapa para habilitar atualização remota.",
    legend:
      "Sem linha = sem vínculo · Tracejada = herança por driver · Sólida = vínculo OTA explícito.",
    launchOta: "Disparo agora ou agendado a partir do popover/menu do nó.",
    updateLinked: "Dispara OTA para os IoTs ligados a esta família.",
  },

  hub: {
    hero:
      "Admin mapa: firmwares e IoTs no canvas. Popovers, menus e modais host-contained para operar sem sair do mapa.",
    branch: "Filial dos IoTs exibidos no canvas, no disparo e nas atualizações.",
    refresh: "Recarrega firmwares, IoTs e atualizações da filial.",
    newDevice: "Cadastra um novo dispositivo IoT nesta filial (modal).",
    newFirmware: "Cria uma nova versão de firmware (modal).",
    kpiPublished: "Versões publicadas e não arquivadas, elegíveis para disparo OTA.",
    kpiLinked: "IoTs com vínculo explícito de família — pré-requisito para OTA.",
    kpiUpdating: "IoTs com atualização autorizada, baixando ou aplicando agora.",
    kpiFailed: "IoTs cuja última atualização falhou — verifique erro e rede.",
    kpiOutdatedSuffix: "desatualizado(s)",
    canvasLegend:
      "Sem linha = sem vínculo · Tracejada = driver (só leitura) · Sólida = vínculo OTA (desvinculável).",
    edgeModesTitle: "Conexões",
    edgeModesHint:
      "Sem linha: IoT sem vínculo e sem match de driver. Tracejada: herança automática pelo driver — não apaga com Desvincular. Sólida: vínculo explícito para OTA — remova com Desvincular ou Delete na seta.",
    edgeNone: "sem linha = sem vínculo",
    edgeDashed: "tracejada = driver (só leitura)",
    edgeSolid: "sólida = vínculo OTA",
    softDeleteDevice: "Soft delete do IoT: desativa operação e polling; o cadastro permanece (filtro Inativos).",
    softDeleteFirmware:
      "Soft delete da versão: arquiva — sai de novos disparos OTA; histórico e jobs antigos permanecem.",
    softDeleteDeviceConfirmTitle: "Desativar IoT (soft delete)?",
    softDeleteDeviceConfirmBody:
      "O dispositivo deixa de ser operado e some do filtro «Todos» como ativo. Reative depois pelo menu ⋯. Não há exclusão definitiva.",
    softDeleteDeviceConfirmLabel: "Desativar IoT",
    softDeleteFirmwareConfirmTitle: "Arquivar versão (soft delete)?",
    softDeleteFirmwareConfirmBody:
      "A versão deixa de ser elegível para novos disparos OTA. Histórico e jobs antigos permanecem. Não há exclusão definitiva.",
    softDeleteFirmwareConfirmLabel: "Arquivar versão",
    menuEditDevice: "Abre o formulário do IoT (rede, vínculo de posto, token) em modal.",
    menuRenameDevice: "Altera só o nome exibido do IoT, sem mudar IP ou vínculo.",
    menuOtaDeviceNow: "Dispara OTA agora para este IoT (exige vínculo sólido ou família publicada compatível).",
    menuOtaDeviceSchedule: "Agenda data/hora para autorizar o download OTA neste IoT.",
    menuUnlinkFirmware:
      "Remove o vínculo sólido (assignedFirmwareKey). Se restar linha tracejada, é herança pelo driver.",
    menuDisableDevice: "Soft delete: desativa o IoT (filtro Inativos). Não apaga o cadastro.",
    menuEnableDevice: "Reativa um IoT desativado e volta a operar/polling.",
    menuEditFirmwareMeta: "Abre o detalhe da versão para editar nome exibido e notas.",
    menuNewFirmwareVersion: "Cria nova versão na mesma família (nova release com sketch/bin).",
    menuOtaFamilyNow: "Dispara OTA agora para os IoTs com vínculo explícito nesta família.",
    menuOtaFamilySchedule: "Agenda OTA para os IoTs vinculados a esta família.",
    menuArchiveFirmware:
      "Soft delete da versão: arquiva — sai de novos disparos; histórico permanece.",
    menuEditFirmwareDraft: "Continua o rascunho: identidade, sketch e binário.",
    menuAttachSource: "Anexa ou atualiza o snapshot do sketch (.ino) desta versão.",
    menuAttachBinary: "Anexa o artefato .bin necessário para publicar.",
    menuPublishFirmware: "Publica a versão (imutável depois). Exige .bin anexado.",
    menuOpenDetails: "Abre o detalhe completo (modal) do IoT ou da versão.",
    panelDevices: "Abre o catálogo de IoTs da filial em painel lateral.",
    panelFirmwares: "Abre o catálogo de firmwares em painel lateral.",
    panelJobs: "Abre a lista de jobs OTA (agendados e em andamento).",
    statusFilter: "Filtra nós do mapa por status (online, offline ou inativos).",
    kpiOutdated: "IoTs com versão instalada diferente da última publicada da família vinculada.",
    kpiJobsChip: "Abre o painel de jobs OTA da filial.",
    catalog: "Catálogo de firmwares no painel lateral — busque por família, versão ou driver.",
    catalogSearch: "Busca por família, versão, driver ou nome exibido.",
    jobs: "Jobs OTA no painel lateral. Abra os detalhes para ver IoT por IoT.",
    jobDetails: "Ver detalhes",
    jobDetailsHint: "Abre o status por dispositivo desta atualização.",
    targetsDialogTitle: "Detalhes da atualização",
    focusCatalogAnchor: "Catálogo de firmwares",
    focusJobsAnchor: "Atualizações OTA",
    mapSearch: "Filtra e destaca nós no mapa.",
    fleetHealth: "Resumo compacto da saúde OTA da frota.",
    collapseFilters: "Recolhe ou expande filtros, KPIs e legenda do mapa.",
    lockNodes: "Bloqueia o arraste dos nós no canvas.",
    bottomBar: "Contagens, jobs ativos e atalhos secundários do mapa.",
  },

  firmwareCreate: {
    hero: "Nova versão: identificação, sketch (.ino) e artefato (.bin) na mesma release.",
    breadcrumb: "Novo firmware",
    sectionIdentity: "Família, driver e versão — imutáveis depois de criar.",
    sectionSource: "Snapshot do sketch da versão. Importar .ino preenche o editor.",
    sectionArtifact: "Binário OTA. Obrigatório para publicar; opcional no rascunho.",
    sectionNotes: "Nome exibido e notas da versão para operadores e admin.",
    sourceField: "Importe o .ino desta versão — o texto fica editável abaixo.",
    sourceEditor: "Cole ou ajuste o sketch. Limite ~256 KiB por versão.",
    artifactField: "Anexe o .bin compilado. O sha256 é calculado no servidor.",
    cancel: "Descarta a versão e volta ao hub OTA.",
    saveDraft: "Cria a versão como rascunho — sketch e bin ainda editáveis.",
    publish: "Cria e publica a versão. Exige artefato .bin anexado.",
  },

  modals: {
    resetTitle: "Confirma zerar o contador físico deste device?",
    resetBody:
      "O valor no hardware volta a zero. A operação fica registrada com seu usuário.",
    factoryResetTitle: "Restaurar configuração de fábrica do chip?",
    factoryResetBody:
      "Apaga Wi-Fi, token e debounce no EEPROM do ESP e reinicia o controlador. O contador em memória zera. O histórico no Production Pulse permanece. O token no cadastro também será limpo.",
    factoryResetConfirm: "Restaurar fábrica",
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
