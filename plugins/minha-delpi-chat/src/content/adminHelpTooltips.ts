/**
 * Ajuda in-app do console admin do chat (feature-help-sync).
 * Textos PT de negócio — sem operationId / paths de API.
 */

export const ADMIN_HELP = {
  overview:
    "Resumo operacional e fila de atenção (ferramentas com falha, bloqueios, candidatos pendentes, regressão falhando, taxa de erro). Endereços do console usam segmentos em inglês (ex.: quality/metrics); atalhos antigos em português continuam abrindo a mesma tela.",
  documents:
    "Base global de conhecimento: upload, metadados curadoriais, reindexação e teste RAG por documento.",
  guidelines:
    "Políticas versionadas (rascunho / publicar / arquivar) que entram no system prompt conforme o ambiente.",
  behaviors:
    "Catálogo global de comportamentos (skills). Skills por agente ficam no Studio do agente.",
  learning:
    "Fila humana: candidatos, vocabulário, memória, regressão e dataset de treino (export).",
  specialization:
    "Catálogo de especialização RAG/tools. A ficha completa do agente (identidade, prompt, actions) fica no Studio.",
  simulation:
    "Playground que usa o mesmo pipeline de produção (prompt, RAG e tools planejadas).",
  metrics:
    "Observabilidade: visão geral com fila de atenção e drill-down por família na sidebar.",
  evaluations:
    "Avaliação humana de respostas (nota, veredito e sugestões para conhecimento/diretrizes).",
  tools:
    "Saúde da plataforma e catálogo OpenAPI. Importe o OpenAPI do provider, vincule as actions ao agente e pergunte em linguagem natural — o roteamento usa o contrato (retrieval + planner). Não é necessário ensinar cada endpoint no registry. Testes de action ficam no Studio do agente.",
  intelligence:
    "Políticas globais do pipeline (RAG, tools, orquestração). O roteamento de tools é OpenAPI-first por padrão (catálogo importado + retrieval/planner); o registry legado só entra se o modo for desligado explicitamente. Não confundir com métricas.",
  security:
    "Proteção de entrada (scan / bloqueio). Eventos cruzam com a Auditoria.",
  audit:
    "Trilha de eventos administrativos e de chat, com filtros e exportação conforme permissão.",
  fineTuneExportOnly:
    "Neste ambiente o fine-tune é só exportação de dataset (JSONL). Deploy local exige Ollama.",
} as const;

export type AdminHelpKey = keyof typeof ADMIN_HELP;
