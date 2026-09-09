/**
 * Ajuda in-app do console admin e do Studio (feature-help-sync).
 * Textos PT de negócio — sem operationId / paths de API.
 *
 * Usar com FieldLabel / SectionHintLabel / hint de ChatAdminNative*Field
 * e AdminTabHeader.helpHint.
 */

export const ADMIN_HELP = {
  pages: {
    overview:
      "Resumo operacional, fila de atenção e Manual por persona (curador / plataforma / auditor). Endereços do console usam segmentos em inglês (ex.: quality/improve); atalhos antigos em português continuam abrindo a mesma tela.",
    documents:
      "Base global de conhecimento: upload, metadados curadoriais, reindexação e teste RAG. Filtros (busca, status, categoria…) ficam na URL para compartilhar a mesma visão.",
    guidelines:
      "Políticas versionadas (rascunho / publicar / arquivar) que entram no system prompt conforme o ambiente.",
    behaviors:
      "Catálogo global de comportamentos (skills). Skills e actions por agente ficam no Studio — use o CTA Abrir Studio nesta tela.",
    learning:
      "Fila humana: candidatos, vocabulário, memória, regressão e dataset de treino (export).",
    learningPipeline:
      "Interruptores do pipeline de aprendizagem (captura, vocabulário, glossário e correção de digitação). Cada knob já explica prós e contras no cartão.",
    learningCandidates:
      "Candidatos aprendidos com o uso. Aprove para promover ao vocabulário ou rejeite para descartar.",
    learningVocabulary:
      "Termos aprovados que o chat reconhece e normaliza. Inclua a forma falada e a forma canônica.",
    learningMemory:
      "Memória operacional persistida: termos e formas normalizadas usadas em follow-ups.",
    learningEvaluation:
      "Casos de regressão: pergunta de entrada e intenção esperada para validar o pipeline.",
    finetuning:
      "Neste ambiente o fine-tune é só exportação de dataset (JSONL). Deploy local exige Ollama.",
    specialization:
      "Catálogo de especialização RAG/tools. A ficha completa do agente (identidade, prompt, actions) edita-se no Studio — CTA Abrir Studio sempre disponível.",
    simulation:
      "Playground que usa o mesmo pipeline de produção (prompt, RAG e tools planejadas).",
    metrics:
      "Observabilidade: visão geral com fila de atenção e drill-down por família na sidebar. A janela temporal (hours=24, 168 ou 720) fica na URL.",
    evaluations:
      "Avaliação humana de respostas (nota, veredito e sugestões para conhecimento/diretrizes).",
    improve:
      "Hub de melhoria contínua (HITL): atalhos para avaliações, candidatos de aprendizagem e feedback nas métricas — filas separadas, sem grid unificado.",
    tools:
      "Saúde da plataforma e catálogo OpenAPI. Importe o OpenAPI do provider, vincule as actions ao agente e pergunte em linguagem natural — o roteamento usa o contrato (retrieval + planner + validação). Pedidos compostos e follow-ups reutilizam o estado estruturado da action, sem cadastrar endpoint no registry. Testes de action ficam no Studio do agente.",
    intelligence:
      "Políticas globais do pipeline (RAG, tools, orquestração). Use presets Rápido, Equilibrado ou Máxima qualidade; Avançado revela knobs individuais. O roteamento de tools é OpenAPI-first. Não confundir com métricas.",
    response:
      "Controla se o seletor Texto / Painel / Automático aparece na sessão do chat. O valor salvo aqui prevalece sobre o ambiente.",
    vision:
      "OCR, desenhos técnicos e limites de extração de documentos anexados. Cada knob já explica impacto no cartão.",
    security:
      "Proteção de entrada (scan / bloqueio). Eventos cruzam com a Auditoria.",
    audit:
      "Trilha de eventos administrativos e de chat. Filtros (busca, contexto, action, traceId, datas) ficam na URL. O diagnóstico da bolha pode abrir esta tela filtrada por traceId (quando presente).",
  },

  shell: {
    search:
      "Busca na árvore de navegação e no índice de conteúdo do admin. Digite o nome da tela, KPI ou conceito.",
    refresh:
      "Recarrega resumos, filas e listas da tela atual sem sair do console.",
    backToChat: "Fecha o console e volta para a conversa.",
  },

  fields: {
    settings: {
      applyToggle:
        "Marque para aplicar este comportamento no pipeline do chat. O cartão acima já descreve o impacto.",
      currentValue:
        "Valor numérico ativo deste parâmetro. Respeite o intervalo indicado no cartão.",
    },
    documents: {
      search: "Filtra a lista por título, categoria ou tags. O filtro fica na URL para compartilhar a visão.",
      status: "Mostra documentos ativos, inativos ou todos da base global.",
      category: "Agrupamento curatorial (ex.: atendimento). Faceta da base global.",
      namespace: "Espaço lógico da fonte (ex.: global:rh) para isolar o RAG.",
      domain: "Domínio de negócio associado ao documento.",
      tag: "Etiqueta livre usada na recuperação e nos filtros.",
      sourceType: "Tipo da fonte (diretriz, glossário, manual, política ou upload).",
      title: "Nome visível na base global e nos testes de recuperação.",
      content: "Texto que será fatiado e indexado na base global.",
      sourceRef: "Identificador estável da origem para reindexação e auditoria.",
      type: "Classificação da peça: diretriz, glossário, manual, política ou upload admin.",
      file: "Arquivo da base global (txt, md, csv, json, docx, xlsx ou pdf).",
      priority: "Prioridade 1–5 na recuperação: maior número sobe na ordenação curatorial.",
      qualityScore: "Nota 0–100 de qualidade editorial; documentos fracos podem ser reindexados ou desativados.",
      tags: "Lista separada por vírgula; entra nos filtros e no RAG.",
    },
    guidelines: {
      title: "Nome curto da política. Aparece na lista e no versionamento.",
      description: "Resumo operacional para quem publica ou audita a diretriz.",
      category: "Família da regra: comportamento, recuperação, ferramentas ou segurança.",
      environment: "Onde a diretriz entra no prompt: global ou só em um ambiente.",
      content: "Texto da regra que o chat deve seguir após a publicação.",
      testQuestion: "Pergunta de teste para ver se a diretriz entra no contexto recuperado.",
      versionGuideline: "Diretriz cujas versões serão comparadas ou restauradas.",
      versionFrom: "Versão inicial da comparação (rascunho ou publicada).",
      versionTo: "Versão destino da comparação.",
      newGuideline: "Abre o editor para criar um rascunho. Publique só depois da revisão.",
    },
    skills: {
      key: "Identificador estável da skill (slug). Não altere depois de vinculada a agentes.",
      label: "Nome visível no catálogo e no Studio.",
      policyFile: "Arquivo de política usado como fallback quando não há flag no metadata.",
      metadataFlag: "Chave no metadata que liga ou desliga a skill no pipeline.",
      legacyFlag: "Flag antiga ainda aceita para compatibilidade; prefira a flag canônica.",
      executionHint: "Dica de quando a skill deve disparar, em linguagem de negócio.",
      derivedKey: "Chave derivada usada internamente na execução.",
      sortOrder: "Ordem de exibição no catálogo. Números menores aparecem primeiro.",
      description: "O que a skill faz e quando o curador deve ativá-la.",
      policyMarkdown: "Política em Markdown que descreve o comportamento esperado.",
      active: "Skills inativas não aparecem para novos vínculos em agentes.",
      openStudio: "Abre a ficha do agente no Studio para ligar skills por agente.",
    },
    learning: {
      candidateStatus: "Filtra candidatos pendentes, aprovados ou rejeitados.",
      term: "Forma que o chat deve reconhecer (como a pessoa escreve).",
      normalized: "Forma canônica usada na normalização e no vocabulário aprovado.",
      meaning: "Definição curta do termo para o glossário operacional.",
      evalInput: "Pergunta ou entrada que o caso de regressão deve simular.",
      evalIntent: "Intenção esperada após o pipeline (ex.: identidade do assistente).",
      datasetName: "Nome do dataset exportado em JSONL para treino externo.",
      sampleStatus: "Filtra amostras capturadas, aprovadas ou rejeitadas.",
      termType: "Classifica o termo (typo, abreviação, expressão ou definição).",
      datasetDescription: "Resumo do dataset exportado para treino externo.",
      approveDataset: "Dataset que receberá as amostras aprovadas nesta tela.",
    },
    specialization: {
      enabled: "Liga o recorte RAG/tools deste agente. Desligado usa só o comportamento global.",
      preset: "Atalho de domínio que preenche namespaces, categorias e tools permitidas.",
      label: "Nome amigável desta especialização na lista admin.",
      domain: "Domínio principal usado para filtrar conhecimento e diretrizes.",
      knowledgeDomains: "Domínios extras, separados por vírgula, incluídos na recuperação.",
      namespaces: "Namespaces da base global que o agente pode consultar.",
      knowledgeCategories: "Categorias de documentos permitidas neste recorte.",
      knowledgeTags: "Tags de documentos usadas como filtro adicional.",
      guidelineCategories: "Categorias de diretrizes injetadas no prompt deste agente.",
      allowedTools: "Tools internas permitidas, separadas por vírgula.",
      includeGlobal: "Também consulta a base global além do recorte de domínio.",
    },
    simulation: {
      question: "Pergunta enviada ao mesmo pipeline de produção (prompt, RAG e tools).",
      agent: "Agente simulado. Vazio usa o agente padrão do chat.",
      session: "Sessão opcional para reutilizar histórico na simulação.",
      executeTools: "Executa tools no sandbox. Desligado só planeja, não chama APIs.",
      generateAnswer: "Gera a resposta final. Desligado mostra só o plano (prompt, RAG e tools).",
      openStudio: "Abre a ficha completa do agente selecionado no Studio.",
    },
    evaluations: {
      search: "Filtra candidatos de avaliação por trecho da pergunta ou da resposta.",
      comment: "Comentário humano que alimenta sugestões de conhecimento e diretrizes.",
      useLlm: "Mais lento; gera sugestões adicionais com base no contexto da resposta.",
    },
    metrics: {
      window:
        "Janela temporal das métricas. O valor (24h, 7 ou 30 dias) fica na URL para compartilhar.",
    },
    tools: {
      agentFilter: "Filtra o catálogo OpenAPI pelas actions vinculadas a um agente.",
      importOpenApi: "Importa o contrato OpenAPI do provider. O roteamento usa o schema, sem cadastrar endpoint à mão.",
    },
    intelligence: {
      advanced: "Mostra todos os knobs de RAG, actions e orquestração. Use presets se não precisar de ajuste fino.",
    },
    security: {
      message: "Cole uma mensagem para testar scan e bloqueio de entrada, sem enviar ao chat.",
      scan: "Analisa a mensagem contra as regras de proteção e registra o evento.",
      openAudit: "Abre a Auditoria filtrada para cruzar eventos de segurança.",
    },
    audit: {
      search: "Busca em ação, usuário, contexto ou hash. O filtro permanece na URL.",
      context: "Origem do evento (admin, chat, conhecimento…). Combina com os demais filtros.",
      action: "Nome da ação auditada (ex.: envio de mensagem ou publicação de diretriz).",
      userId: "Identificador do usuário que disparou o evento.",
      traceId: "Correlaciona a requisição com o diagnóstico da conversa.",
      dateFrom: "Início do intervalo. Combine com a data final para recortar a trilha.",
      dateTo: "Fim do intervalo (inclusivo no dia).",
      exportJson: "Baixa os eventos filtrados em JSON para análise externa.",
      exportCsv: "Baixa os eventos filtrados em CSV.",
      colAction: "Ação registrada na trilha (o que aconteceu).",
      colContext: "Contexto operacional do evento.",
      colTrace: "Identificador de correlação com a conversa ou o fluxo admin.",
      colUser: "Quem disparou o evento.",
      colDate: "Data e hora do registro.",
    },
    overview: {
      rbac: "Capacidades do seu perfil neste console (curadoria, auditoria e operações sensíveis).",
      attention: "Itens que pedem ação: filas, falhas e atalhos para a tela dona do problema.",
    },
    improve: {
      evaluations: "Notas, vereditos e sugestões sobre respostas do assistente.",
      candidates: "Fila de candidatos para vocabulário, memória e regressão.",
      feedback: "Thumbs e sinais de feedback na observabilidade de Qualidade.",
    },
  },

  kpis: {
    guidelines: {
      total: "Todas as diretrizes, em qualquer status.",
      active: "Publicadas e em vigor.",
      draft: "Rascunhos ainda não publicados.",
      archived: "Arquivadas; não entram no prompt.",
    },
    skills: {
      total: "Skills no catálogo global.",
      active: "Visíveis no catálogo dos agentes.",
      inactive: "Desligadas; não aparecem para novos vínculos.",
    },
    agents: {
      total: "Agentes no catálogo de especialização.",
      enabled: "Agentes ativos para uso.",
      specialized: "Com domínio RAG e ferramentas configurados.",
      disabled: "Agentes inativos neste catálogo.",
    },
    learning: {
      pendingHighConfidence: "Alta confiança:",
      createdTotal: "No total:",
      approved: "Aprovados:",
      rejected: "Rejeitados:",
      vocabularyTotal: "No vocabulário:",
      candidateTypes: "Candidatos por tipo (definição / typo).",
      forgotten: "Esquecidas:",
      evalActive: "Casos ativos:",
      samplesCaptured: "Capturadas:",
      ragBreakdown: "Glossário e memória no índice.",
    },
    documents: {
      total: "Todos os documentos da base global, ativos e inativos.",
      active: "Documentos ativos na base global.",
      inactive: "Documentos desativados; não entram na recuperação.",
      pending: "Ativos ainda sem trechos indexados — reindexe ou aguarde o pipeline.",
    },
    simulate: {
      agents: "Agentes disponíveis para o sandbox de simulação.",
      sessions: "Sessões que podem ser reutilizadas como histórico opcional.",
      result: "Última simulação: prompt, recuperação e ferramentas previstas.",
    },
    evaluations: {
      total: "Avaliações humanas já registradas.",
      average: "Nota média (1–5) nas avaliações carregadas.",
      helpful: "Respostas com nota 4 ou 5.",
      recent: "Avaliações nas últimas 24 horas.",
    },
    security: {
      blocked: "Mensagens barradas no chat pela proteção de entrada.",
      events: "Eventos de segurança registrados na auditoria.",
      scans: "Testes feitos por este painel.",
      total: "Total de eventos na janela selecionada.",
    },
    audit: {
      matching: "Eventos que correspondem aos filtros atuais.",
      pageRows: "Linhas exibidas na tabela desta página.",
      pageEvents: "Eventos carregados na página atual.",
      timeline: "Eventos na página; a timeline agrupa por dia.",
    },
    tools: {
      health: "Verificações operacionais do catálogo e do provedor.",
      routes: "Rotas OpenAPI administradas no catálogo.",
      exposed: "Itens expostos ao catálogo do usuário.",
    },
    qualityUnified: {
      csat: "Satisfação (positivo ÷ total de feedbacks) na janela.",
      activeUsers: "Pessoas que conversaram na janela.",
      messagesPerSession: "Média de mensagens por sessão.",
      latency: "Tempo médio de resposta na janela.",
      chipCtr: "Cliques em sugestões ÷ impressões.",
      securityBlocks: "Mensagens bloqueadas pela proteção de entrada.",
    },
    feedback: {
      csat: "Feedback positivo dividido pelo total.",
      positive: "Avaliações positivas (joinha) na janela.",
      negative: "Avaliações negativas na janela.",
      lostContext: "Sinais de perda de contexto no feedback.",
    },
    drawing: {
      turns: "Turnos com análise de desenho técnico na janela.",
      codes: "Códigos únicos detectados nos desenhos.",
      critical: "Erros críticos somados nas análises.",
      exported: "Turnos em que o relatório foi exportado.",
      analyserOk: "Análises concluídas com sucesso.",
      pdf: "Turnos com anexo PDF na conversa.",
    },
    vision: {
      turns: "Turnos com visão de documento na janela.",
      legible: "Execuções classificadas como legíveis.",
      latency: "Tempo médio do pipeline de visão quando medido.",
    },
    sql: {
      skillOn: "Conversas com a skill SQL avançada ativa.",
      destructive: "Comandos destrutivos detectados e recusados.",
      empty: "Execuções sem linhas retornadas.",
      ready: "Turnos com consulta pronta para refinamento.",
      usage: "Uso detectado em SQL gerado ou analisado.",
      catalogHint: "Turnos que sugeriram explorar o catálogo de tabelas.",
    },
    intent: {
      turns: "Turnos com roteamento de intenção na janela.",
      ambiguous: "Pedidos com escopo operacional incerto (desambiguação).",
      compound: "Pedidos compostos (operacional + texto/web).",
      web: "Rotas com pesquisa web explícita.",
    },
    errors: {
      classified: "Respostas com classificação de erro ou vazio.",
      recoveryUi: "Respostas com chips ou fluxo de recuperação.",
      noDenial: "Respostas que não afirmaram inexistência de dados.",
      retryPlan: "Respostas com plano para reexecutar a consulta.",
      recoverClicks: "Chips do grupo recuperar acionados.",
      recoverySuccess: "Recuperações bem-sucedidas na janela.",
    },
    webSearch: {
      turns: "Turnos com pesquisa web concluída ou tentada.",
      official: "Pesquisas que citaram fonte oficial.",
      lowConfidence: "Respostas com confiança classificada como baixa.",
      empty: "Busca vazia ou sem fonte confiável.",
      redacted: "Dados sensíveis removidos antes da busca.",
      skipped: "Consultas não enviadas ao buscador.",
      chips: "Atalhos como «Só fontes oficiais» ou «Buscar em inglês».",
      reasons: "Motivos específicos de pesquisa web.",
    },
    interactivity: {
      turns: "Turnos com bloco consolidado de sugestões.",
      shown: "Total de sugestões mostradas (principais + extras).",
      clicks: "Sugestões acionadas pela pessoa.",
      ctr: "Cliques dividido pelas impressões.",
      overflow: "Respostas que agruparam sugestões extras.",
    },
    typing: {
      chips: "Sugestões de correção exibidas após a pausa na digitação.",
      acceptClicks: "Cliques em enviar o texto corrigido.",
      keepOriginal: "Pessoa manteve o texto original.",
      acceptRate: "Aceites dividido pelas ofertas na janela.",
      sent: "Mensagens enviadas já com a correção aceita.",
      perTurn: "Correções por turno aceito (auditoria).",
    },
    presentation: {
      rich: "Turnos com gráfico, tabela ou KPI e decisão registrada.",
      interactions: "Trocas de vista, eixo, tipo e exportações.",
      perAnswer: "Eventos por resposta rica (média na janela).",
      viewSwitch: "Respostas em que a pessoa trocou texto, tabela ou gráfico.",
      toTable: "Trocas de vista que foram para tabela.",
      axis: "Respostas ricas com mudança de eixo.",
      filters: "Filtros de filial, operador, centro e similares.",
      downloads: "Downloads de gráfico.",
    },
    memory: {
      turns: "Respostas com snapshot de memória na auditoria.",
      resolution: "Taxa em que a memória resolveu o follow-up.",
      lowAssert: "Assertividade baixa ou entidade não reutilizada.",
      lowScore: "Pontuação contextual abaixo do limiar.",
      unresolved: "Memória não resolveu a referência sozinha.",
      lostContext: "Feedback de perda de contexto na janela.",
    },
    textTask: {
      turns: "Turnos com tarefa textual na janela.",
      mixed: "Consulta operacional e redação no mesmo fluxo.",
      validatorFail: "Respostas com falha no validador textual.",
      versions: "Atualizações com histórico de versões na lousa.",
      direct: "Pedidos com entrega direta, sem explicação longa.",
      fromFile: "Tarefas textuais originadas de arquivo anexado.",
    },
  },

  studio: {
    search: "Filtra a lista por nome ou categoria do agente.",
    showInactive: "Inclui agentes desativados na lista. Só quem gerencia agentes vê esta opção.",
    create: "Cria um agente novo e abre a ficha no Studio.",
    name: "Nome visível na lista, no chat e nos atalhos.",
    category: "Agrupamento livre (ex.: Produtos) para achar o agente na lista.",
    icon: "Ícone exibido na lista e no seletor de agentes.",
    description: "Resumo do que o agente faz, para quem escolhe o especialista.",
    visibility: "Quem pode ver e usar o agente (privado, compartilhado ou oficial).",
    instructions: "Instruções de sistema: papel, tom e limites. Não cole segredos aqui.",
    icebreakers: "Perguntas iniciais sugeridas ao abrir o agente.",
    maxTools: "Limite de tools por turno para este agente.",
    promptTemplate:
      "Atalho que preenche as instruções com um modelo. Revise o texto antes de publicar.",
    responseStyle: "Tom da resposta deste agente (objetivo, técnico, executivo ou detalhado).",
    agentEnabled: "Agentes inativos não aparecem para uso na lista nem no chat.",
    allowActions: "Permite que este agente chame as APIs configuradas na ficha de actions.",
    allowFiles: "Permite documentos e fontes de conhecimento neste agente.",
    allowCanvas: "Permite a lousa (canvas) nas conversas deste agente.",
    allowRead: "Permite operações de leitura nesta API.",
    allowWrite: "Permite operações que alteram dados nesta API.",
    allowAdmin: "Permite operações administrativas nesta API.",
    requireWriteConfirmation: "Pede confirmação humana antes de ações que alteram dados.",
    copyActions: "Na duplicação, copia as APIs e actions desta ficha.",
    copySources: "Na duplicação, copia as fontes de conhecimento deste agente.",
    shareRole: "Papel de quem recebe o agente: só visualizar ou também editar a ficha.",
    openApiUrl: "Endereço do contrato OpenAPI usado para importar as rotas.",
    privacyPolicy: "URL da política de privacidade desta API, visível na governança.",
    schema: "Contrato OpenAPI em JSON. Atualize as rotas após alterar a URL.",
    authMode: "Como o agente autentica nesta API. Não cole o segredo nas instruções.",
    apiKey: "Chave usada nas chamadas. Fica no provedor, não no prompt.",
    authHeader: "Nome do cabeçalho HTTP que transporta a chave.",
    authScheme: "Formato do token no cabeçalho (Bearer, Basic ou personalizado).",
    clientId: "Identificador OAuth do cliente nesta API.",
    clientSecret: "Segredo OAuth. Não compartilhe no prompt nem na descrição.",
    authorizationUrl: "URL de autorização OAuth desta API.",
    tokenUrl: "URL para obter o token OAuth.",
    oauthScope: "Escopos OAuth pedidos nesta integração.",
    testPathParam: "Valor do parâmetro de rota exigido pelo contrato OpenAPI.",
    testQueryName: "Nome do parâmetro de consulta, como no OpenAPI.",
    testQueryValue: "Valor enviado neste teste. Não publica a action.",
    runTest: "Dispara a chamada de teste com os parâmetros preenchidos.",
    skillToggle: "Liga ou desliga esta skill só neste agente. O catálogo global fica no admin.",
    actionsName: "Nome da API no catálogo do agente.",
    actionsBaseUrl: "Endereço base usado nas chamadas desta API.",
    actionsAuth: "Como o agente autentica nesta API (chave, OAuth ou nenhum).",
    actionsTest: "Envia uma chamada de teste com os parâmetros preenchidos, sem publicar.",
    openActions: "Abre o catálogo OpenAPI e os testes deste agente.",
    openSkills: "Abre as skills vinculadas a este agente.",
  },

  ctas: {
    openStudio: "Abre a ficha completa do agente (identidade, prompt, skills e actions).",
    newGuideline: "Cria um rascunho de diretriz. Publique só após revisão.",
    ingest: "Envia o arquivo ou o texto para a base global e inicia a indexação.",
    previewPipeline: "Mostra como o conteúdo seria fatiado antes de ingerir.",
  },
} as const;

type HelpLeaf = string | { readonly [key: string]: HelpLeaf };

function collectPaths(
  node: HelpLeaf,
  prefix: string,
  out: Map<string, string>,
): void {
  if (typeof node === "string") {
    out.set(prefix, node);
    return;
  }
  for (const [key, value] of Object.entries(node)) {
    const next = prefix ? `${prefix}.${key}` : key;
    collectPaths(value, next, out);
  }
}

const ADMIN_HELP_INDEX: Map<string, string> = (() => {
  const map = new Map<string, string>();
  collectPaths(ADMIN_HELP as HelpLeaf, "", map);
  return map;
})();

/** Resolve texto de help por chave dotted (ex.: `fields.documents.search`). */
export function getAdminHelp(key: string): string {
  return ADMIN_HELP_INDEX.get(key) ?? "";
}

/** Todas as chaves registradas — testes e auditoria de cobertura. */
export function listAdminHelpKeys(): string[] {
  return [...ADMIN_HELP_INDEX.keys()].sort();
}

export type AdminHelpPages = typeof ADMIN_HELP.pages;
export type AdminHelpPageKey = keyof AdminHelpPages;
