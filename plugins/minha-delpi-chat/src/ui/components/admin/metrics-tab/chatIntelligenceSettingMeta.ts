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
  {
    id: "tools",
    title: "Ferramentas internas",
    description:
      "Ativa ou desativa tools do pipeline base (não confundir com actions OpenAPI do agente).",
  },
];

export const CHAT_INTELLIGENCE_TOGGLE_META: Record<
  | "externalActionSemanticRankEnabled"
  | "chatToolRouterEnabled"
  | "chatHistorySummaryEnabled"
  | "ragHybridEnabled"
  | "ragRerankEnabled"
  | "ragFtsEnabled"
  | "ragPreferKeywordSearch"
  | "nativeToolCallingEnabled"
  | "agenticLoopEnabled"
  | "fastPathEnabled"
  | "assistantIdentityDirectEnabled"
  | "operationalFastPathEnabled"
  | "externalActionDirectResponseEnabled"
  | "preferApiExternaProvider"
  | "multiActionEnabled"
  | "paginationAutoFetchEnabled"
  | "externalActionEmbeddingOnImport"
  | "webSearchEnabled"
  | "webSearchDirectResponseEnabled"
  | "webSearchAutoAugmentEnabled",
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
  ragPreferKeywordSearch: {
    title: "Preferir busca por palavra-chave (sem híbrido)",
    summary:
      "Quando o RAG híbrido está desligado, tenta FTS/keyword antes do vetor puro.",
    pros: [
      "Melhor para códigos e termos exatos sem custo do modo híbrido completo.",
      "Útil em bases pequenas com vocabulário técnico previsível.",
    ],
    cons: [
      "Só faz sentido com FTS ativo; sem híbrido pode perder recall semântico.",
      "Menos robusto que o par híbrido + rerank em bases grandes.",
    ],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "neutral",
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
  operationalFastPathEnabled: {
    title: "Fast path operacional",
    summary:
      "Atalha o pipeline para perguntas operacionais reconhecidas (estoque, produto, rotas REST), pulando etapas genéricas.",
    pros: [
      "Respostas mais rápidas em consultas DELPI típicas.",
      "Menos tokens e menos chamadas LLM intermediárias.",
    ],
    cons: [
      "Perguntas ambíguas podem ir direto demais sem desambiguação.",
      "Depende de intents e actions bem calibradas.",
    ],
    speedWhenEnabled: "fast",
    qualityWhenEnabled: "neutral",
  },
  externalActionDirectResponseEnabled: {
    title: "Resposta direta pós-action",
    summary:
      "Quando uma action retorna dados estruturados, o chat pode responder sem passar tudo pelo LLM.",
    pros: [
      "Menor latência e custo após consultas API.",
      "Apresentação consistente via presenter canônico.",
    ],
    cons: [
      "Perguntas que pedem análise criativa podem ficar mais secas.",
      "Exige presenter alinhado ao contrato da API.",
    ],
    speedWhenEnabled: "fast",
    qualityWhenEnabled: "neutral",
  },
  preferApiExternaProvider: {
    title: "Priorizar provider api_externa",
    summary:
      "Dá preferência a actions do catálogo api_externa/api-delpi na seleção quando há empate.",
    pros: [
      "Reduz escolha de actions legadas ou duplicadas.",
      "Alinha homologação local com rotas REST modernas.",
    ],
    cons: [
      "Pode suprimir actions customizadas se nomes colidirem.",
      "Desligue ao testar providers alternativos.",
    ],
    speedWhenEnabled: "neutral",
    qualityWhenEnabled: "higher",
  },
  multiActionEnabled: {
    title: "Múltiplas actions por turno",
    summary:
      "Permite planejar e executar mais de uma action na mesma mensagem quando necessário.",
    pros: [
      "Suporta perguntas compostas (ex.: estoque + preço).",
      "Evita resposta incompleta em fluxos operacionais encadeados.",
    ],
    cons: [
      "Aumenta latência proporcional ao número de chamadas API.",
      "Mais difícil depurar qual action falhou.",
    ],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
  },
  paginationAutoFetchEnabled: {
    title: "Buscar páginas extras automaticamente",
    summary:
      "Quando a API pagina resultados, o chat pode buscar páginas adicionais antes de responder.",
    pros: [
      "Listas longas chegam completas sem o usuário pedir “próxima página”.",
      "Melhora tabelas operacionais com muitos itens.",
    ],
    cons: [
      "Multiplica chamadas HTTP e tempo de resposta.",
      "Pode estourar timeout em APIs lentas.",
    ],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
  },
  externalActionEmbeddingOnImport: {
    title: "Embedding ao importar OpenAPI",
    summary:
      "Recalcula embedding de cada action durante o botão “Atualizar rotas” (import síncrono).",
    pros: [
      "Ranking semântico fica pronto imediatamente após import.",
      "Menos passo manual de reindexação.",
    ],
    cons: [
      "Import demora muito com catálogos grandes (~135 rotas).",
      "Recomendado desligar até import assíncrono (Playbook 16).",
    ],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "neutral",
    tip: "Desligado + reindex separado acelera o cadastro de rotas novas.",
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
  fastPathEnabled: {
    title: "Fast path geral (mensagens curtas)",
    summary:
      "Atalha turnos muito curtos ou triviais (saudação, utilitários) com prompt reduzido.",
    pros: [
      "Respostas instantâneas para “oi”, “obrigado”, hora/data.",
      "Economia de tokens em interações sociais.",
    ],
    cons: [
      "Mensagens curtas mas operacionais podem perder contexto se mal classificadas.",
      "Limite de caracteres do fast path continua no servidor.",
    ],
    speedWhenEnabled: "fast",
    qualityWhenEnabled: "lower",
  },
  assistantIdentityDirectEnabled: {
    title: "Resposta direta de identidade do assistente",
    summary:
      "Responde “quem é você / o que faz” sem acionar tools nem RAG pesado.",
    pros: [
      "Resposta imediata e estável sobre capacidades do agente.",
      "Evita alucinação em perguntas de identidade.",
    ],
    cons: [
      "Não personaliza com dados dinâmicos do turno.",
      "Perguntas mistas (identidade + operação) podem precisar de follow-up.",
    ],
    speedWhenEnabled: "fast",
    qualityWhenEnabled: "neutral",
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
  webSearchDirectResponseEnabled: {
    title: "Resposta direta pós-pesquisa web",
    summary:
      "Formata resultados da web sem reescrever tudo pelo LLM quando o modo direto está ativo.",
    pros: [
      "Menor latência após a busca externa.",
      "Citações mais fiéis aos snippets retornados.",
    ],
    cons: [
      "Menos prosa fluida; tom pode ficar mais técnico.",
      "Análises comparativas podem precisar do LLM.",
    ],
    speedWhenEnabled: "fast",
    qualityWhenEnabled: "neutral",
  },
  webSearchAutoAugmentEnabled: {
    title: "Complemento automático com web",
    summary:
      "O pipeline pode sugerir pesquisa web quando a confiança do RAG interno é baixa.",
    pros: [
      "Cobre lacunas da base curada sem o usuário pedir explicitamente.",
      "Útil para temas externos à DELPI.",
    ],
    cons: [
      "Pode disparar busca web indevida se heurística errar.",
      "Aumenta latência e dependência de rede.",
    ],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
  },
  webSearchEnabled: {
    title: "Pesquisa web (tool interna)",
    summary:
      "Permite ao chat consultar a internet quando a pergunta pede dados externos ou atuais. Requer SearXNG/Tavily configurado no servidor.",
    pros: [
      "Responde perguntas sobre mercado, notícias ou referências fora da base DELPI.",
      "Complementa RAG interno sem misturar fontes corporativas.",
    ],
    cons: [
      "Depende de serviço de busca e rede — latência e disponibilidade variam.",
      "Resultados externos exigem cautela em ambientes corporativos.",
    ],
    speedWhenEnabled: "slow",
    qualityWhenEnabled: "higher",
    tip: "Chaves de API e URL do provedor continuam no servidor (Docker); aqui você só liga ou desliga o uso no chat.",
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
  ragIdentityQuestionMinScore: {
    title: "Score mínimo RAG (perguntas de identidade)",
    summary:
      "Limiar mais baixo ao buscar trechos para “quem é você / o que faz”, ampliando recall em FAQs.",
    pros: [
      "Encontra políticas e textos de identidade mesmo com match fraco.",
      "Evita resposta vazia em bases pequenas.",
    ],
    cons: [
      "Trechos pouco relacionados podem entrar no prompt.",
      "Ajuste fino necessário se respostas ficarem genéricas.",
    ],
    speedNote: "Impacto leve; afeta sobretudo qualidade em perguntas de identidade.",
    qualityNote: "↓ score = mais recall; ↑ score = contexto mais estrito.",
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
