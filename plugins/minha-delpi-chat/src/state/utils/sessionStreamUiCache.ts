import type {
  ChatSource,
  ChatStreamActivityEntry,
  ChatToolCall,
} from "../../data/api/chatTypes";

export type SessionStreamUiSnapshot = {
  activityLog: ChatStreamActivityEntry[];
  status: string | null;
  sources: ChatSource[];
  toolCalls: ChatToolCall[];
};

const EMPTY_SNAPSHOT: SessionStreamUiSnapshot = {
  activityLog: [],
  status: null,
  sources: [],
  toolCalls: [],
};

const cache = new Map<string, SessionStreamUiSnapshot>();

export function getSessionStreamUi(sessionId: string): SessionStreamUiSnapshot {
  return cache.get(sessionId) ?? EMPTY_SNAPSHOT;
}

export function patchSessionStreamUi(
  sessionId: string,
  patch: Partial<SessionStreamUiSnapshot>,
): SessionStreamUiSnapshot {
  const current = getSessionStreamUi(sessionId);
  const next: SessionStreamUiSnapshot = {
    activityLog: patch.activityLog ?? current.activityLog,
    status: patch.status !== undefined ? patch.status : current.status,
    sources: patch.sources ?? current.sources,
    toolCalls: patch.toolCalls ?? current.toolCalls,
  };

  cache.set(sessionId, next);
  return next;
}

export function clearSessionStreamUi(sessionId: string): void {
  cache.delete(sessionId);
}
