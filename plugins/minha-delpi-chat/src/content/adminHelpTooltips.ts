/**
 * Ajuda in-app do console admin do chat (feature-help-sync).
 * Textos PT de negócio — sem operationId / paths de API.
 */

export const ADMIN_HELP = {
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
  security:
    "Proteção de entrada (scan / bloqueio). Eventos cruzam com a Auditoria.",
  audit:
    "Trilha de eventos administrativos e de chat. Filtros (busca, contexto, action, traceId, datas) ficam na URL. O diagnóstico da bolha pode abrir esta tela filtrada por traceId (quando presente).",
  fineTuneExportOnly:
    "Neste ambiente o fine-tune é só exportação de dataset (JSONL). Deploy local exige Ollama.",
} as const;

export type AdminHelpKey = keyof typeof ADMIN_HELP;
