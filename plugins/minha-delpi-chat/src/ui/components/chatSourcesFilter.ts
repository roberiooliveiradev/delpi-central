import type { ChatSource } from "../../data/api/chatTypes";

const GLOBAL_SOURCE_TYPES = new Set([
  "global",
  "admin_upload",
  "admin_preview_upload",
  "diretriz",
  "guideline",
  "admin_guideline",
]);

export function isGeneralChatSource(source: ChatSource): boolean {
  const scope = String(source.scope ?? "").trim().toLowerCase();

  if (scope === "global" || scope === "agent_source") {
    return true;
  }

  if (scope === "project_source" || scope === "session_source") {
    return false;
  }

  if (source.projectId || source.sessionId || source.attachmentId) {
    return false;
  }

  if (source.agentKey) {
    return true;
  }

  const sourceType = String(source.sourceType ?? "").trim().toLowerCase();

  if (GLOBAL_SOURCE_TYPES.has(sourceType)) {
    return true;
  }

  const sourceRef = String(source.sourceRef ?? "").trim().toLowerCase();

  if (sourceRef.startsWith("global:")) {
    return true;
  }

  if (!scope) {
    return true;
  }

  return sourceType === "global";
}

export function filterVisibleChatSources(sources?: ChatSource[]): ChatSource[] {
  if (!sources?.length) {
    return [];
  }

  return sources.filter((source) => !isGeneralChatSource(source));
}
