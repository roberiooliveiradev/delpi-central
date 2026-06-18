import type {
  ChatAgentPreviewResponse,
  ChatMessage,
  ChatSource,
  ChatStreamActivityEntry,
  ChatToolCall,
} from "../data/api/chatTypes";

export const AGENT_BUILDER_PREVIEW_SESSION_ID = "agent-builder-preview";

export type PreviewTurn = {
  role: "user" | "assistant";
  content: string;
};

export const PREVIEW_REQUEST_TIMEOUT_MS = 120_000;

const PREVIEW_LOADING_PHASES: Array<Pick<ChatStreamActivityEntry, "id" | "phase" | "message">> = [
  {
    id: "preview-rag",
    phase: "rag",
    message: "Consultando a base de conhecimento...",
  },
  {
    id: "preview-guidelines",
    phase: "guidelines",
    message: "Aplicando diretrizes do agente...",
  },
  {
    id: "preview-tools",
    phase: "tools",
    message: "Preparando ferramentas autorizadas...",
  },
  {
    id: "preview-answer",
    phase: "answer",
    message: "Gerando resposta...",
  },
];

export function createPreviewLoadingActivityLog(
  activePhaseIndex = 0,
): ChatStreamActivityEntry[] {
  const now = Date.now();

  return PREVIEW_LOADING_PHASES.map((phase, index) => ({
    ...phase,
    state: index < activePhaseIndex ? "done" : index === activePhaseIndex ? "active" : "done",
    at: now + index,
    level: index < activePhaseIndex ? "success" : "info",
  })).filter((_, index) => index <= activePhaseIndex);
}

export function createAgentPreviewChatMessage(
  role: PreviewTurn["role"],
  content: string,
  metadata: ChatMessage["metadata"] = null,
): ChatMessage {
  return {
    id: `preview-${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    session_id: AGENT_BUILDER_PREVIEW_SESSION_ID,
    role,
    content,
    metadata,
    created_at: new Date().toISOString(),
  };
}

export function toPreviewPreviousMessages(messages: ChatMessage[]): PreviewTurn[] {
  return messages
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map((message) => ({
      role: message.role as PreviewTurn["role"],
      content: message.content,
    }));
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

export function mapPreviewToolCalls(raw: unknown): ChatToolCall[] {
  if (!Array.isArray(raw)) {
    return [];
  }

  return raw
    .map((item) => {
      const record = asRecord(item);

      if (!record) {
        return null;
      }

      const metadata = asRecord(record.metadata);

      return {
        name: typeof record.name === "string" ? record.name : undefined,
        arguments:
          asRecord(record.arguments) ??
          (record.arguments && typeof record.arguments === "object"
            ? (record.arguments as Record<string, unknown>)
            : {}),
        reason: typeof record.reason === "string" ? record.reason : null,
        metadata: metadata
          ? {
              ...metadata,
              actionId:
                typeof metadata.actionId === "string"
                  ? metadata.actionId
                  : typeof record.name === "string"
                    ? record.name
                    : null,
              responsePreview:
                typeof metadata.responsePreview === "string"
                  ? metadata.responsePreview
                  : typeof record.status === "string"
                    ? record.status
                    : null,
            }
          : null,
      } as ChatToolCall;
    })
    .filter((item): item is ChatToolCall => item !== null);
}

export function mapPreviewSources(result: ChatAgentPreviewResponse): ChatSource[] {
  const chunks = Array.isArray(result.chunks) ? result.chunks : [];
  const matchedDocuments = Array.isArray(result.matchedDocuments)
    ? result.matchedDocuments
    : [];

  if (chunks.length > 0) {
    return chunks.map((chunk, index) => {
      const record = asRecord(chunk) ?? {};

      return {
        id: String(record.id ?? record.documentId ?? `preview-source-${index + 1}`),
        documentId:
          typeof record.documentId === "string"
            ? record.documentId
            : typeof record.id === "string"
              ? record.id
              : undefined,
        title: typeof record.title === "string" ? record.title : "Documento",
        sourceType: typeof record.sourceType === "string" ? record.sourceType : null,
        sourceRef: typeof record.sourceRef === "string" ? record.sourceRef : null,
        score: typeof record.score === "number" ? record.score : null,
      } satisfies ChatSource;
    });
  }

  return matchedDocuments.map((document, index) => {
    const record = asRecord(document) ?? {};

    return {
      id: String(record.id ?? `preview-document-${index + 1}`),
      title: typeof record.title === "string" ? record.title : "Documento",
      score: typeof record.score === "number" ? record.score : null,
      sourceType: typeof record.sourceType === "string" ? record.sourceType : null,
      sourceRef: typeof record.sourceRef === "string" ? record.sourceRef : null,
    } satisfies ChatSource;
  });
}

export function resolvePreviewAnswer(result: ChatAgentPreviewResponse): string {
  const answerPreview =
    typeof result.answerPreview === "string" ? result.answerPreview.trim() : "";
  const answer = typeof result.answer === "string" ? result.answer.trim() : "";

  return answerPreview || answer || "Sem resposta na pré-visualização.";
}

export function buildPreviewActivityLogFromResult(
  result: ChatAgentPreviewResponse,
): ChatStreamActivityEntry[] {
  const now = Date.now();
  const entries: ChatStreamActivityEntry[] = [];
  const chunks = Array.isArray(result.chunks) ? result.chunks : [];
  const guidelines = Array.isArray(result.appliedGuidelines) ? result.appliedGuidelines : [];
  const tools = mapPreviewToolCalls(result.plannedToolCalls ?? result.toolCalls ?? []);

  if (chunks.length > 0) {
    entries.push({
      id: "preview-rag",
      phase: "rag",
      message: `Contexto recuperado (${chunks.length} trecho${chunks.length > 1 ? "s" : ""}).`,
      state: "done",
      level: "success",
      at: now,
    });
  }

  if (guidelines.length > 0) {
    entries.push({
      id: "preview-guidelines",
      phase: "guidelines",
      message: `${guidelines.length} diretriz${guidelines.length > 1 ? "es" : ""} aplicada${guidelines.length > 1 ? "s" : ""}.`,
      state: "done",
      level: "success",
      at: now + 1,
    });
  }

  tools.forEach((tool, index) => {
    const label = tool.name?.trim() || "ferramenta";

    entries.push({
      id: `preview-tool-${index}-${label}`,
      phase: "tool",
      group: "tools",
      target: label,
      message: tool.reason?.trim() || `Consultando ${label}...`,
      state: "done",
      level: "success",
      at: now + 2 + index,
    });
  });

  entries.push({
    id: "preview-answer",
    phase: "answer",
    message: "Resposta gerada.",
    state: "done",
    level: "success",
    at: now + 10,
  });

  return entries;
}

export function buildAgentPreviewAssistantMessage(
  result: ChatAgentPreviewResponse,
): ChatMessage {
  const toolCalls = mapPreviewToolCalls(result.plannedToolCalls ?? result.toolCalls ?? []);
  const sources = mapPreviewSources(result);

  return createAgentPreviewChatMessage("assistant", resolvePreviewAnswer(result), {
    toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
    sources: sources.length > 0 ? sources : undefined,
  });
}
