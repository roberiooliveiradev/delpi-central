import { useCallback, useEffect, useState } from "react";

import {
  createChatSession,
  listChatMessages,
  listChatSessions,
} from "../../data/api/chatApi";
import type { ChatMessage, ChatSession } from "../../data/api/chatTypes";
import { useChatStreaming } from "./useChatStreaming";

type UseChatSessionOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function useChatSession(options: UseChatSessionOptions = {}) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { isStreaming, streamMessage, cancelStreaming } = useChatStreaming({
    getAccessToken: options.getAccessToken,
  });

  const loadSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    setError(null);

    try {
      const data = await listChatSessions({
        getAccessToken: options.getAccessToken,
      });

      setSessions(data);

      setActiveSession((current) => current ?? data[0] ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar sessões.");
    } finally {
      setIsLoadingSessions(false);
    }
  }, [options.getAccessToken]);

  const selectSession = useCallback((session: ChatSession) => {
    setStreamingAnswer("");
    setActiveSession(session);
  }, []);

  const startSession = useCallback(async () => {
    setError(null);

    try {
      const session = await createChatSession(
        {
          title: "Nova conversa",
          context: "geral",
        },
        {
          getAccessToken: options.getAccessToken,
        },
      );

      setSessions((current) => [session, ...current]);
      setActiveSession(session);
      setMessages([]);
      setStreamingAnswer("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar sessão.");
    }
  }, [options.getAccessToken]);

  const loadMessages = useCallback(
    async (sessionId: string) => {
      setIsLoadingMessages(true);
      setError(null);

      try {
        const data = await listChatMessages(sessionId, {
          getAccessToken: options.getAccessToken,
        });

        setMessages(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar mensagens.");
      } finally {
        setIsLoadingMessages(false);
      }
    },
    [options.getAccessToken],
  );

  const sendMessage = useCallback(async () => {
    const message = draft.trim();

    if (!message || !activeSession || isStreaming) {
      return;
    }

    setError(null);
    setStreamingAnswer("");

    try {
      await streamMessage({
        sessionId: activeSession.id,
        message,
        context: activeSession.context ?? "geral",
        onToken: (token) => {
          setStreamingAnswer((current) => current + token);
        },
        onDone: async () => {
          setDraft("");
          setStreamingAnswer("");
          await loadMessages(activeSession.id);
          await loadSessions();
        },
        onError: (message) => {
          setError(message);
        },
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }

      setError(err instanceof Error ? err.message : "Erro ao enviar mensagem.");
    }
  }, [
    activeSession,
    draft,
    isStreaming,
    loadMessages,
    loadSessions,
    streamMessage,
  ]);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (!activeSession) {
      setMessages([]);
      return;
    }

    void loadMessages(activeSession.id);
  }, [activeSession, loadMessages]);

  return {
    sessions,
    activeSession,
    messages,
    draft,
    streamingAnswer,
    isLoadingSessions,
    isLoadingMessages,
    isStreaming,
    error,
    setDraft,
    sendMessage,
    cancelStreaming,
    loadSessions,
    startSession,
    selectSession,
  };
}
