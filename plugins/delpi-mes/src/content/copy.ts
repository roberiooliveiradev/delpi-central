export const DELPI_MES_COPY = {
  productName: "Delpi MES",
  productDescription: "Supervisão e análise gerencial da execução industrial da Delpi.",
  monitoring: {
    title: "Monitoramento Industrial",
    description: "Estrutura pronta para acompanhamento dos centros de trabalho e seus estados operacionais.",
    guidance: "Selecione a filial e use esta área como ponto de entrada para a visão operacional consolidada.",
  },
  downtimes: {
    title: "Paradas",
    description: "Consulta gerencial dos eventos reais de parada do MES — manuais, automáticas e autônomas.",
    guidance: "Filtre por período, centro de trabalho, motivo, origem e situação da classificação. Selecione uma ocorrência para ver o detalhe.",
  },
  history: {
    title: "Histórico",
    description: "Base de navegação preparada para análise da linha do tempo dos runs de produção.",
    guidance: "O detalhamento preservará os tempos calculados pelo owner dos fatos MES.",
  },
  registrations: {
    title: "Cadastros",
    description: "Configurações globais utilizadas pelo Delpi MES.",
    globalScope: "Cadastro global",
    globalScopeHint: "As alterações são válidas para todas as filiais.",
    downtimeReasons: {
      title: "Motivos de parada",
      description: "Gerencie os motivos utilizados na classificação das paradas MES.",
      action: "Gerenciar",
    },
  },
  downtimesManagement: {
    classifyHint: "O motivo vem do catálogo canônico de paradas. Alterar o motivo registra a reclassificação no histórico.",
    classifyDenied: "Seu perfil permite consultar a parada, mas não alterar a classificação.",
    notePlaceholder: "Detalhe a causa, se necessário",
    treatDenied: "Seu perfil permite consultar a triagem, mas não registrá-la.",
    treatmentEmpty: "Nenhuma triagem registrada para esta parada.",
    analysisPlaceholder: "O que foi observado durante a parada?",
    justificationPlaceholder: "Por que esta decisão de tratamento?",
    referralDisclaimer: "A solicitação será enviada ao departamento de Processos com o contexto desta parada.",
    referralDenied: "Seu perfil não permite abrir solicitações de problema de processo.",
    concludeBlocked: "A solicitação vinculada precisa estar concluída para encerrar o tratamento.",
  },
  help: {
    branch: "A filial faz parte da URL para manter navegação, recarga e compartilhamento no mesmo contexto.",
    permissions: "As áreas visíveis refletem suas permissões; o backend valida novamente cada consulta.",
    downtimesPeriod: "Os períodos seguem o dia civil do fuso operacional do MES (America/Sao_Paulo), independente do fuso do navegador. Em período personalizado, a data final cobre o dia inteiro.",
    downtimesClassification: "Confirmada: motivo classificado e confirmado. Pendente: parada sem motivo confirmado, incluindo registros históricos incompletos.",
    downtimesStatus:
      "Aberta: parada ainda em andamento contada até agora. Encerrada: parada com fim registrado. O estado é derivado dos fatos MES pelo Production Control.",
    downtimesStatesIndependence:
      "Encerramento e classificação são condições independentes: uma parada pode estar encerrada e ainda aguardar a confirmação do motivo.",
    downtimesAdvancedFilters:
      "Filtros adicionais para refinar o universo consultado. O contador mostra quantos estão aplicados, mesmo com o painel recolhido.",
    downtimesExport:
      "Arquivos gerados pelo backend com todas as paradas do universo autorizado que atendem aos filtros — nunca apenas a página exibida. Cada arquivo identifica a filial, os filtros e a referência temporal do cálculo.",
    downtimesManagement:
      "Classificar atribui o motivo canônico da parada; a triagem registra análise e causa; o encaminhamento abre uma solicitação para o departamento de Processos. Todas as ações ficam no histórico auditável da parada.",
    downtimesDuration: "Paradas encerradas usam fim menos início; paradas abertas contam até o relógio do servidor.",
    downtimesAnalytics:
      "Indicadores calculados pelo Production Control sobre todas as paradas elegíveis do período — nunca apenas sobre a página exibida. Tempo total usa a união temporal por centro de trabalho: sobreposições de registros não contam o mesmo segundo duas vezes. A soma atribuída às ocorrências pode superar esse total quando o histórico contém paradas sobrepostas.",
    downtimesAnalyticsDaily:
      "Cada dia civil (America/Sao_Paulo) mostra o tempo parado ou a quantidade de ocorrências que intersectam o dia. Uma parada que atravessa a meia-noite pode contar em dois dias — no indicador global ela conta apenas uma vez.",
    downtimesAnalyticsHeatmap:
      "Concentração por dia da semana e hora (America/Sao_Paulo). A duração de cada parada é distribuída pelos horários efetivamente atravessados. O mapa é descritivo — não filtra a lista.",
    downtimesAnalyticsPareto:
      "Motivos ordenados pelo tempo perdido no período. O percentual usa o tempo atribuído às ocorrências; paradas sem motivo confirmado formam o grupo Pendente de classificação. Clique em um motivo para filtrar a lista.",
    downtimesAnalyticsCenters:
      "Centros de trabalho ordenados pelo tempo parado no período, incluindo paradas autônomas sem ordem de produção. Clique em um centro para filtrar a lista.",
    downtimesAnalyticsPartial:
      "O período excedeu o limite de fatos processados de uma vez; os valores exibidos são parciais. Reduza o período ou refine os filtros para ver o total completo.",
    downtimesInsights:
      "Análise avançada calculada pelo Production Control sobre o mesmo universo de paradas dos indicadores: comparação com o período anterior imediatamente equivalente, reincidência real por centro de trabalho e motivo, ocorrências críticas segundo parâmetros do processo industrial e evidências das ações concluídas.",
    downtimesInsightsRecurrence:
      "Agrupa ocorrências reais (registros distintos, sem duplicar paradas) por centro de trabalho e motivo confirmado no período. Clique em um grupo para filtrar a lista por aquele centro e motivo.",
    downtimesInsightsCritical:
      "Paradas abertas além do limite parametrizado e rajadas de reincidência acima do mínimo configurado. Os limites são governados pelo processo industrial no Production Control — nunca definidos nesta tela. Sem parâmetro aprovado, a regra fica inativa.",
    downtimesInsightsEffectiveness:
      "Para cada tratamento concluído, compara as ocorrências do mesmo motivo no mesmo centro de trabalho em janelas iguais antes e depois da conclusão.",
    downtimesInsightsEvidenceNote:
      "Evidência observacional antes/depois — uma queda não prova que a ação causou a melhora.",
    downtimesInsightsTelemetryGaps:
      "Há centros de trabalho sensorizados sem telemetria confiável recente: a análise não inventa paradas para esses períodos e os resultados podem estar subestimados.",
  },
} as const;
