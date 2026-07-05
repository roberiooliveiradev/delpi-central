type SessionStreamEntry = {
  controller: AbortController;
};

export type ChatStreamSessionRegistry = {
  isStreaming: (sessionId: string) => boolean;
  getActiveController: (sessionId: string) => AbortController | undefined;
  register: (sessionId: string, controller: AbortController) => void;
  unregister: (sessionId: string, controller: AbortController) => void;
  abort: (sessionId: string) => void;
  abortAll: () => void;
};

export function createChatStreamSessionRegistry(): ChatStreamSessionRegistry {
  const streams = new Map<string, SessionStreamEntry>();

  return {
    isStreaming(sessionId) {
      return streams.has(sessionId);
    },

    getActiveController(sessionId) {
      return streams.get(sessionId)?.controller;
    },

    register(sessionId, controller) {
      streams.get(sessionId)?.controller.abort();
      streams.set(sessionId, { controller });
    },

    unregister(sessionId, controller) {
      if (streams.get(sessionId)?.controller === controller) {
        streams.delete(sessionId);
      }
    },

    abort(sessionId) {
      streams.get(sessionId)?.controller.abort();
      streams.delete(sessionId);
    },

    abortAll() {
      for (const entry of streams.values()) {
        entry.controller.abort();
      }

      streams.clear();
    },
  };
}
