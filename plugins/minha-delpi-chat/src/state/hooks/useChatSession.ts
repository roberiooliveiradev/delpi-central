import { useCallback, useEffect, useState } from "react";

import {
  createChatSession,
  listChatMessages,
  listChatSessions,
  renameChatSession,
} from "../../data/api/chatApi";
import type {
  ChatMessage,
  ChatSession,
  ChatSource,
  ChatToolCall,
} from "../../data/api/chatTypes";
import { useChatStreaming } from "./useChatStreaming";

type UseChatSessionOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

function createOptimisticUserMessage(
  sessionId: string,
  content: string,
): ChatMessage {
  return {
    id: `optimistic-${Date.now()}`,
    session_id: sessionId,
    role: "user",
    content,
    metadata: {
      optimistic: true,
    },
    created_at: new Date().toISOString(),
  };
}

export function useChatSession(options: UseChatSessionOptions = {}) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [streamingSources, setStreamingSources] = useState<ChatSource[]>([]);
  const [streamingToolCalls, setStreamingToolCalls] = useState<ChatToolCall[]>([]);
  const [streamingStatus, setStreamingStatus] = useState<string | null>(null);
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
    setStreamingSources([]);
    setStreamingToolCalls([]);
    setStreamingStatus("Preparando sua pergunta...");
    setStreamingStatus(null);
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
      setStreamingSources([]);
      setStreamingToolCalls([]);
      setStreamingStatus(null);
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

  const renameSession = useCallback(
    async (sessionId: string, title: string) => {
      const normalizedTitle = title.trim();

      if (!normalizedTitle) {
        setError("Informe um título para a conversa.");
        return null;
      }

      setError(null);

      try {
        const updatedSession = await renameChatSession(
          sessionId,
          normalizedTitle,
          {
            getAccessToken: options.getAccessToken,
          },
        );

        setSessions((current) =>
          current.map((session) =>
            session.id === sessionId ? updatedSession : session,
          ),
        );

        setActiveSession((current) =>
          current?.id === sessionId ? updatedSession : current,
        );

        return updatedSession;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao renomear conversa.");
        return null;
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
    setDraft("");
    setMessages((current) => [
      ...current,
      createOptimisticUserMessage(activeSession.id, message),
    ]);
    setStreamingAnswer("");
    setStreamingSources([]);
    setStreamingToolCalls([]);
    setStreamingStatus("Preparando sua pergunta...");

    try {
      await streamMessage({
        sessionId: activeSession.id,
        message,
        context: activeSession.context ?? "geral",
        onSources: (sources) => {
          setStreamingSources(sources);
          setStreamingStatus(
            sources.length > 0
              ? "Consultando a base de conhecimento..."
              : "Verificando contexto autorizado...",
          );
        },
        onToolCalls: (toolCalls) => {
          setStreamingToolCalls(toolCalls);
          setStreamingStatus(
            toolCalls.length > 0
              ? "Consultando sistemas autorizados..."
              : "Gerando resposta...",
          );
        },
        onToken: (token) => {
          setStreamingStatus(null);
          setStreamingAnswer((current) => current + token);
        },
        onDone: async () => {
          setDraft("");
          setStreamingAnswer("");
          setStreamingSources([]);
          setStreamingToolCalls([]);
          setStreamingStatus(null);
          await loadMessages(activeSession.id);
          await loadSessions();
        },
        onError: (message) => {
          setStreamingStatus(null);
          setError(message);
        },
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }

      setStreamingStatus(null);
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
    streamingSources,
    streamingToolCalls,
    streamingStatus,
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
    renameSession,
  };
}
