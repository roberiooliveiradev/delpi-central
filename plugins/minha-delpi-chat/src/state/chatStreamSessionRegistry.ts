export type ChatStreamSessionRegistry = {
  isStreaming: (sessionId: string) => boolean;
  register: (sessionId: string, controller: AbortController) => void;
  unregister: (sessionId: string, controller: AbortController) => void;
  abort: (sessionId: string) => void;
  abortAll: () => void;
};

export function createChatStreamSessionRegistry(): ChatStreamSessionRegistry {
  const streams = new Map<string, AbortController>();

  return {
    isStreaming(sessionId) {
      return streams.has(sessionId);
    },

    register(sessionId, controller) {
      streams.get(sessionId)?.abort();
      streams.set(sessionId, controller);
    },

    unregister(sessionId, controller) {
      if (streams.get(sessionId) === controller) {
        streams.delete(sessionId);
      }
    },

    abort(sessionId) {
      streams.get(sessionId)?.abort();
      streams.delete(sessionId);
    },

    abortAll() {
      for (const controller of streams.values()) {
        controller.abort();
      }

      streams.clear();
    },
  };
}
