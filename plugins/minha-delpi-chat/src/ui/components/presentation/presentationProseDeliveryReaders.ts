import type {
  ChatProseDeliveryMode,
  ChatTemplateProseArchive,
  ChatToolCall,
} from "../../../data/api/chatTypes";

import { isLlmProseDecoupledMetadata } from "./presentationMarkdownNormalization";

export function shouldBlockTemplateProseMetadata(
  metadata: Record<string, unknown> | null | undefined,
): boolean {
  if (!metadata || typeof metadata !== "object") {
    return false;
  }

  if (isLlmProseDecoupledMetadata(metadata)) {
    return true;
  }

  return metadata.dataOnlyPresentation === true;
}

export function getProseDeliveryModeFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatProseDeliveryMode | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const metadata = toolCall.metadata;

    if (!metadata || metadata.ok === false) {
      continue;
    }

    const mode = String(metadata.proseDeliveryMode || "").trim().toLowerCase();

    if (mode === "template" || mode === "llm" || mode === "direct") {
      return mode;
    }
  }

  return null;
}

export function getTemplateProseArchiveFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatTemplateProseArchive | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const archive = toolCall.metadata?.templateProseArchive;

    if (archive && typeof archive === "object") {
      return archive;
    }
  }

  return null;
}

/** Archive é só para fatos LLM na API — nunca usar como markdown renderizável. */
export function resolveRenderableHumanizedLines(
  metadata: Record<string, unknown> | null | undefined,
): string[] {
  if (!metadata || typeof metadata !== "object") {
    return [];
  }

  if (shouldBlockTemplateProseMetadata(metadata)) {
    return [];
  }

  const humanized = metadata.humanizedSummary;

  if (!humanized || typeof humanized !== "object") {
    return [];
  }

  const lines = (humanized as { linhas?: unknown }).linhas;

  if (!Array.isArray(lines)) {
    return [];
  }

  return lines.map((line) => String(line || "").trim()).filter(Boolean);
}

export function resolveRenderableHumanizedDetailLines(
  metadata: Record<string, unknown> | null | undefined,
): string[] {
  if (!metadata || typeof metadata !== "object") {
    return [];
  }

  if (shouldBlockTemplateProseMetadata(metadata)) {
    return [];
  }

  const humanized = metadata.humanizedSummary;

  if (!humanized || typeof humanized !== "object") {
    return [];
  }

  const lines = (humanized as { linhas_detalhe?: unknown }).linhas_detalhe;

  if (!Array.isArray(lines)) {
    return [];
  }

  return lines.map((line) => String(line || "").trim()).filter(Boolean);
}

export function resolveRenderableTemplateMarkdown(
  metadata: Record<string, unknown> | null | undefined,
): string {
  if (!metadata || typeof metadata !== "object") {
    return "";
  }

  if (shouldBlockTemplateProseMetadata(metadata)) {
    return "";
  }

  const textPresentation = metadata.textPresentation;

  if (!textPresentation || typeof textPresentation !== "object") {
    return "";
  }

  return String((textPresentation as { markdown?: string }).markdown || "").trim();
}
