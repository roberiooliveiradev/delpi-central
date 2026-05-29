export type SettingSpeedImpact = "fast" | "neutral" | "slow";
export type SettingQualityImpact = "lower" | "neutral" | "higher";

export type ChatIntelligenceSettingMeta = {
  title: string;
  summary: string;
  pros: readonly string[];
  cons: readonly string[];
  speedWhenEnabled: SettingSpeedImpact;
  qualityWhenEnabled: SettingQualityImpact;
  tip?: string;
};

export type ChatIntelligenceSectionMeta = {
  id: string;
  title: string;
  description: string;
};

export const CHAT_INTELLIGENCE_SECTIONS: ChatIntelligenceSectionMeta[] = [
  {
    id: "rag",
    title: "Recuperação de conhecimento (RAG)",
    description:
      "Controla como o chat busca trechos em fontes, manuais e base curada antes de montar a resposta.",
  },
  {
    id: "actions",
    title: "Actions e APIs externas",
    description:
      "Define como o sistema escolhe qual action chamar quando a pergunta é operacional (estoque, produto, etc.).",
  },
  {
    id: "orchestration",
    title: "Orquestração do LLM",
    description:
      "Recursos avançados de roteamento, tool-calling e múltiplas rodadas de ferramentas.",
  },
  {
    id: "context",
    title: "Contexto da conversa",
    description: "Como o histórico longo entra no prompt sem estourar o limite de tokens.",
  },
];

export const CHAT_INTELLIGENCE_TOGGLE_META: Record<
  | "externalActionSemanticRankEnabled"
  | "chatToolRouterEnabled"
  | "chatHistorySummaryEnabled"
  | "ragHybridEnabled"
  | "ragRerankEnabled"
  | "ragFtsEnabled"
  | "nativeToolCallingEnabled"
  | "agenticLoopEnabled",
  ChatIntelligenceSettingMeta
> = {
  ragHybridEnabled: {
    title: "RAG híbrido (vetor + palavras-chave)",
    summary:
      "Combina busca semântica por embedding com correspondência lexical. Ajuda quando o usuário cita códigos, siglas ou termos exatos.",
    pros: [
      "Melhor recall em perguntas com SKU, código ou nomenclatura interna.",
      "Reduz respostas genéricas quando o vetor sozinho erra o termo.",
    ],
    cons: [
      "Consulta extra no banco e fusão de resultados.",
      "Requer FTS ativo para a parte lexical funcionar bem.",
    ],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
    tip: "Recomendado em produção quando há documentos técnicos ou tabelas de produto.",
  },
  ragFtsEnabled: {
    title: "Busca FTS no Postgres (keyword RAG)",
    summary:
      "Ativa full-text search no Postgres para a parte por palavra-chave do RAG híbrido.",
    pros: [
      "Encontra trechos com match exato de termos raros.",
      "Complementa embeddings em bases com muitos identificadores.",
    ],
    cons: [
      "Depende de índice/coluna FTS configurados.",
      "Pouco efeito se o RAG híbrido estiver desligado.",
    ],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
    tip: "Ligue junto com RAG híbrido; sozinho não substitui a busca vetorial.",
  },
  ragRerankEnabled: {
    title: "Rerank pós-híbrido no RAG",
    summary:
      "Reordena os candidatos do RAG híbrido antes de enviar ao LLM, priorizando os trechos mais relevantes.",
    pros: [
      "Prompt mais limpo com menos ruído.",
      "Respostas mais fiéis à pergunta em bases grandes.",
    ],
    cons: [
      "Etapa extra de scoring após a busca.",
      "Ganho modesto se a base for pequena ou já bem curada.",
    ],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
  },
  externalActionSemanticRankEnabled: {
    title: "Ranking semântico de actions",
    summary:
      "Ordena actions permitidas do agente por similaridade semântica com a pergunta, antes das regras determinísticas.",
    pros: [
      "Escolha de API mais precisa com muitas actions parecidas.",
      "Menos chamadas erradas em agentes com catálogo grande.",
    ],
    cons: [
      "Exige embeddings das actions indexados.",
      "Pequeno custo extra por mensagem operacional.",
    ],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
    tip: "Após alterar actions, use “Reindexar embeddings”.",
  },
  chatToolRouterEnabled: {
    title: "Router LLM de ferramentas",
    summary:
      "Usa uma chamada LLM dedicada para decidir se a mensagem precisa de RAG, action ou resposta direta.",
    pros: [
      "Melhor desambiguação em perguntas ambíguas ou mistas.",
      "Reduz acionamento indevido de tools em conversa casual.",
    ],
    cons: [
      "Adiciona latência de uma inferência antes da resposta principal.",
      "Custo de tokens extra por turno quando ativo.",
    ],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
    tip: "Útil com muitos agentes/skills; pode ser excessivo em fluxos 100% operacionais.",
  },
  nativeToolCallingEnabled: {
    title: "Tool-calling nativo do LLM (vLLM/Ollama)",
    summary:
      "Delega a escolha de ferramentas ao formato nativo do modelo (function/tool calling), quando suportado.",
    pros: [
      "Integração mais natural com modelos instruídos para tools.",
      "Pode simplificar o pipeline em setups compatíveis.",
    ],
    cons: [
      "Comportamento varia entre providers/modelos.",
      "Pode conflitar com router e loop agentic se tudo estiver ligado.",
    ],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "neutral",
    tip: "Teste com o modelo de produção antes de ativar em massa.",
  },
  agenticLoopEnabled: {
    title: "Loop agentic de ferramentas",
    summary:
      "Permite múltiplas rodadas: o LLM pode chamar uma tool, ler o resultado e decidir a próxima ação.",
    pros: [
      "Suporta fluxos multi-etapa (ex.: buscar produto → estoque → resumir).",
      "Melhora completude em perguntas compostas.",
    ],
    cons: [
      "Aumenta latência e custo proporcional ao número de passos.",
      "Risco de loops ou respostas longas se o limite de passos for alto.",
    ],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
    tip: "Mantenha “Máx. passos” baixo (1–2) salvo casos muito controlados.",
  },
  chatHistorySummaryEnabled: {
    title: "Resumo de histórico longo",
    summary:
      "Condensa mensagens antigas em um resumo quando a conversa ultrapassa o budget de contexto.",
    pros: [
      "Conversas longas continuam coerentes sem estourar tokens.",
      "Reduz perda de contexto em sessões extensas.",
    ],
    cons: [
      "Chamada extra de LLM ao resumir.",
      "Detalhes finos de mensagens antigas podem ser omitidos.",
    ],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "neutral",
    tip: "Qualidade depende do modelo de resumo; monitore conversas com muitos turnos.",
  },
};

export const CHAT_INTELLIGENCE_NUMBER_META = {
  ragContextMinScore: {
    title: "Score mínimo RAG",
    summary:
      "Descarta trechos recuperados abaixo deste score antes de montar o contexto enviado ao LLM.",
    pros: [
      "Valores mais altos (ex.: 0,45+) deixam o prompt mais enxuto.",
      "Menos ruído e alucinação a partir de trechos fracos.",
    ],
    cons: [
      "Muito alto pode omitir contexto útil (menor recall).",
      "Muito baixo inclui trechos irrelevantes e aumenta tokens.",
    ],
    speedNote: "↑ score = menos texto no prompt → resposta tende a ficar mais rápida.",
    qualityNote: "↑ score = mais precisão, mas pode perder nuances; ↓ score = mais recall.",
    min: 0,
    max: 1,
    step: 0.01,
  },
  externalActionSemanticMinScore: {
    title: "Score mínimo action semântica",
    summary:
      "Ignora candidatos de action cuja similaridade semântica com a pergunta fique abaixo deste limiar.",
    pros: [
      "Evita acionar APIs erradas por match fraco.",
      "Complementa regras determinísticas do pipeline.",
    ],
    cons: [
      "Alto demais pode bloquear action correta em perguntas vagas.",
      "Baixo demais reintroduz ruído no ranking.",
    ],
    speedNote: "Impacto pequeno na latência; afeta sobretudo acerto da primeira tool.",
    qualityNote: "↑ score = mais conservador; ↓ score = mais permissivo.",
    min: 0,
    max: 1,
    step: 0.01,
  },
  agenticLoopMaxSteps: {
    title: "Máx. passos do loop agentic",
    summary:
      "Limite de rodadas tool → LLM no loop agentic. Cada passo extra é uma inferência + chamada externa.",
    pros: [
      "Mais passos permitem fluxos encadeados mais completos.",
      "1 passo é previsível e rápido para a maioria dos casos.",
    ],
    cons: [
      "Cada passo adicional aumenta tempo de resposta e custo.",
      "3 passos só faz sentido com monitoramento e timeouts ajustados.",
    ],
    speedNote: "↑ passos = resposta mais lenta (multiplica tools + LLM).",
    qualityNote: "↑ passos = respostas mais completas em perguntas compostas.",
    min: 1,
    max: 3,
    step: 1,
  },
} as const;

export const SPEED_IMPACT_LABELS: Record<SettingSpeedImpact, string> = {
  fast: "Mais rápido",
  neutral: "Velocidade neutra",
  slow: "Mais lento",
};

export const QUALITY_IMPACT_LABELS: Record<SettingQualityImpact, string> = {
  lower: "Pode reduzir qualidade",
  neutral: "Qualidade neutra",
  higher: "Melhora qualidade",
};
