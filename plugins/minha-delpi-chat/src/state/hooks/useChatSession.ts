import { useCallback, useEffect, useState } from "react";

import {
  createChatSession,
  listChatMessages,
  listChatSessions,
} from "../../data/api/chatApi";
import type { ChatMessage, ChatSession } from "../../data/api/chatTypes";

type UseChatSessionOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function useChatSession(options: UseChatSessionOptions = {}) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    setError(null);

    try {
      const data = await listChatSessions({
        getAccessToken: options.getAccessToken,
      });

      setSessions(data);

      if (!activeSession && data.length > 0) {
        setActiveSession(data[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar sessões.");
    } finally {
      setIsLoadingSessions(false);
    }
  }, [activeSession, options.getAccessToken]);

  const selectSession = useCallback((session: ChatSession) => {
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
    isLoadingSessions,
    isLoadingMessages,
    error,
    setDraft,
    loadSessions,
    startSession,
    selectSession,
  };
}
