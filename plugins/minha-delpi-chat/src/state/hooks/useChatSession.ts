import { useCallback, useEffect, useRef, useState } from "react";

import {
  archiveChatSession,
  createChatSession,
  deleteChatSession,
  listChatMessages,
  listChatSessions,
  upsertChatMessageFeedback,
  pinChatSession,
  renameChatSession,
  unarchiveChatSession,
  unpinChatSession,
  updateChatMessage,
  uploadChatAttachment,
} from "../../data/api/chatApi";
import type {
  ChatAttachment,
  ChatMessage,
  ChatSession,
  ChatSource,
  ChatToolCall,
} from "../../data/api/chatTypes";
import { useChatStreaming } from "./useChatStreaming";

type UseChatSessionOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  projectId?: string | null;
  agentKey?: string | null;
};

function createOptimisticUserMessage(
  sessionId: string,
  content: string,
  attachments: { id: string; original_filename: string; size_bytes: number; content_type: string | null; status: string }[] = [],
): ChatMessage {
  return {
    id: `optimistic-${Date.now()}`,
    session_id: sessionId,
    role: "user",
    content,
    metadata: {
      optimistic: true,
      attachments,
    },
    created_at: new Date().toISOString(),
  };
}

export function useChatSession(options: UseChatSessionOptions = {}) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [archivedSessions, setArchivedSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [streamingSources, setStreamingSources] = useState<ChatSource[]>([]);
  const [streamingToolCalls, setStreamingToolCalls] = useState<ChatToolCall[]>([]);
  const [streamingStatus, setStreamingStatus] = useState<string | null>(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingArchivedSessions, setIsLoadingArchivedSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const skipNextSessionLoadRef = useRef(false);

  const { isStreaming, streamMessage, cancelStreaming: cancelStreamingBase } =
    useChatStreaming({
      getAccessToken: options.getAccessToken,
    });

  const cancelStreaming = useCallback(() => {
    cancelStreamingBase();
    setStreamingStatus(null);
    setIsSending(false);
  }, [cancelStreamingBase]);

  const loadSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    setError(null);

    try {
      const data = await listChatSessions({
        getAccessToken: options.getAccessToken,
      });

      setSessions(data);

      setActiveSession((current) => {
        if (!current) {
          return null;
        }

        return data.some((session) => session.id === current.id) ? current : null;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar sessões.");
    } finally {
      setIsLoadingSessions(false);
    }
  }, [options.getAccessToken]);

  const loadArchivedSessions = useCallback(async () => {
    setIsLoadingArchivedSessions(true);
    setError(null);

    try {
      const data = await listChatSessions({
        getAccessToken: options.getAccessToken,
        archived: true,
      });

      setArchivedSessions(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro ao carregar conversas arquivadas.",
      );
    } finally {
      setIsLoadingArchivedSessions(false);
    }
  }, [options.getAccessToken]);

  const selectSession = useCallback((session: ChatSession) => {
    setStreamingAnswer("");
    setStreamingSources([]);
    setStreamingToolCalls([]);
    setStreamingStatus(null);
    setMessages([]);
    setActiveSession(session);
  }, []);

  const startSession = useCallback(async () => {
    setError(null);
    setActiveSession(null);
    setMessages([]);
    setDraft("");
    setStreamingAnswer("");
    setStreamingSources([]);
    setStreamingToolCalls([]);
    setStreamingStatus(null);
  }, []);

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

  const deleteSession = useCallback(
    async (sessionId: string) => {
      setError(null);

      try {
        await deleteChatSession(sessionId, {
          getAccessToken: options.getAccessToken,
        });

        setSessions((current) =>
          current.filter((session) => session.id !== sessionId),
        );

        setActiveSession((current) => {
          if (current?.id !== sessionId) {
            return current;
          }

          const nextSession = sessions.find((session) => session.id !== sessionId) ?? null;
          return nextSession;
        });

        if (activeSession?.id === sessionId) {
          setMessages([]);
        }

        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao excluir conversa.");
        return false;
      }
    },
    [activeSession?.id, options.getAccessToken, sessions],
  );

  const setMessageFeedback = useCallback(
    async (messageId: string, rating: -1 | 1 | null) => {
      if (!activeSession) {
        return;
      }

      await upsertChatMessageFeedback(activeSession.id, messageId, rating, {
        getAccessToken: options.getAccessToken,
      });

      setMessages((current) =>
        current.map((message) =>
          message.id === messageId
            ? {
                ...message,
                user_feedback: rating,
              }
            : message,
        ),
      );
    },
    [activeSession, options.getAccessToken],
  );

  const editMessage = useCallback(
    async (messageId: string, content: string) => {
      const normalizedContent = content.trim();

      if (!normalizedContent) {
        setError("Informe uma mensagem.");
        return null;
      }

      setError(null);

      try {
        const updatedMessage = await updateChatMessage(
          messageId,
          normalizedContent,
          {
            getAccessToken: options.getAccessToken,
          },
        );

        setMessages((current) =>
          current.map((message) =>
            message.id === messageId ? updatedMessage : message,
          ),
        );

        return updatedMessage;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao editar mensagem.");
        return null;
      }
    },
    [options.getAccessToken],
  );

  const reuseMessage = useCallback((content: string) => {
    setDraft(content);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  function replaceSession(updatedSession: ChatSession) {
    setSessions((current) =>
      current.map((session) =>
        session.id === updatedSession.id ? updatedSession : session,
      ),
    );

    setArchivedSessions((current) =>
      current.map((session) =>
        session.id === updatedSession.id ? updatedSession : session,
      ),
    );

    setActiveSession((current) =>
      current?.id === updatedSession.id ? updatedSession : current,
    );
  }

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

  const pinSession = useCallback(
    async (sessionId: string) => {
      setError(null);

      try {
        const updatedSession = await pinChatSession(sessionId, {
          getAccessToken: options.getAccessToken,
        });

        replaceSession(updatedSession);
        await loadSessions();

        return updatedSession;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao fixar conversa.");
        return null;
      }
    },
    [loadSessions, options.getAccessToken],
  );

  const unpinSession = useCallback(
    async (sessionId: string) => {
      setError(null);

      try {
        const updatedSession = await unpinChatSession(sessionId, {
          getAccessToken: options.getAccessToken,
        });

        replaceSession(updatedSession);
        await loadSessions();

        return updatedSession;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao desafixar conversa.");
        return null;
      }
    },
    [loadSessions, options.getAccessToken],
  );

  const archiveSession = useCallback(
    async (sessionId: string) => {
      setError(null);

      try {
        const updatedSession = await archiveChatSession(sessionId, {
          getAccessToken: options.getAccessToken,
        });

        setSessions((current) =>
          current.filter((session) => session.id !== sessionId),
        );
        setArchivedSessions((current) => [updatedSession, ...current]);

        setActiveSession((current) => {
          if (current?.id !== sessionId) {
            return current;
          }

          return sessions.find((session) => session.id !== sessionId) ?? null;
        });

        if (activeSession?.id === sessionId) {
          setMessages([]);
        }

        return updatedSession;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao arquivar conversa.");
        return null;
      }
    },
    [activeSession?.id, options.getAccessToken, sessions],
  );

  const unarchiveSession = useCallback(
    async (sessionId: string) => {
      setError(null);

      try {
        const updatedSession = await unarchiveChatSession(sessionId, {
          getAccessToken: options.getAccessToken,
        });

        setArchivedSessions((current) =>
          current.filter((session) => session.id !== sessionId),
        );
        setSessions((current) => [updatedSession, ...current]);

        return updatedSession;
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Erro ao restaurar conversa.",
        );
        return null;
      }
    },
    [options.getAccessToken],
  );

  const finishSending = useCallback(() => {
    setIsSending(false);
  }, []);

  const sendMessage = useCallback(async (params: { attachments?: File[] } = {}) => {
    const message = draft.trim();

    if (!message || isStreaming || isSending) {
      return;
    }

    const optimisticId = `optimistic-${Date.now()}`;
    let sessionForMessage = activeSession;

    setError(null);
    setDraft("");
    setIsSending(true);
    setStreamingAnswer("");
    setStreamingSources([]);
    setStreamingToolCalls([]);
    setStreamingStatus(
      activeSession
        ? "Preparando sua pergunta..."
        : "Criando conversa e preparando sua pergunta...",
    );

    setMessages((current) => [
      ...current,
      {
        ...createOptimisticUserMessage(
          sessionForMessage?.id ?? "pending",
          message,
        ),
        id: optimisticId,
      },
    ]);

    try {
      if (!sessionForMessage) {
        sessionForMessage = await createChatSession(
          {
            title: "Nova conversa",
            context: "geral",
            projectId: options.projectId ?? null,
            agentKey: options.agentKey ?? null,
          },
          {
            getAccessToken: options.getAccessToken,
          },
        );

        skipNextSessionLoadRef.current = true;
        setSessions((current) => [sessionForMessage!, ...current]);
        setActiveSession(sessionForMessage);
        setMessages((current) =>
          current.map((item) =>
            item.id === optimisticId
              ? {
                  ...item,
                  session_id: sessionForMessage!.id,
                }
              : item,
          ),
        );
      }

      const uploadedAttachments: ChatAttachment[] = [];

      for (const file of params.attachments ?? []) {
        setStreamingStatus(`Enviando arquivo ${file.name}...`);

        const uploaded = await uploadChatAttachment(
          sessionForMessage.id,
          file,
          {
            getAccessToken: options.getAccessToken,
          },
        );

        uploadedAttachments.push(uploaded);
      }

      const attachmentIds = uploadedAttachments.map((attachment) => attachment.id);
      const attachmentPreview = uploadedAttachments.map((attachment) => ({
        id: attachment.id,
        original_filename: attachment.original_filename,
        size_bytes: attachment.size_bytes,
        content_type: attachment.content_type,
        status: attachment.status,
      }));

      if (attachmentPreview.length > 0) {
        setMessages((current) =>
          current.map((item) =>
            item.id === optimisticId
              ? {
                  ...item,
                  metadata: {
                    ...item.metadata,
                    optimistic: true,
                    attachments: attachmentPreview,
                  },
                }
              : item,
          ),
        );
      }

      await streamMessage({
        sessionId: sessionForMessage.id,
        message,
        context: sessionForMessage.context ?? "geral",
        attachmentIds,
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
          finishSending();
          await loadMessages(sessionForMessage!.id);
          await loadSessions();
        },
        onError: (streamError) => {
          setStreamingStatus(null);
          setError(streamError);
          finishSending();
        },
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        finishSending();
        return;
      }

      setStreamingStatus(null);
      setError(err instanceof Error ? err.message : "Erro ao enviar mensagem.");
      finishSending();
    }
  }, [
    activeSession,
    draft,
    finishSending,
    isSending,
    isStreaming,
    loadMessages,
    loadSessions,
    options.agentKey,
    options.getAccessToken,
    options.projectId,
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

    if (skipNextSessionLoadRef.current) {
      skipNextSessionLoadRef.current = false;
      return;
    }

    void loadMessages(activeSession.id);
  }, [activeSession, loadMessages]);

  return {
    sessions,
    archivedSessions,
    activeSession,
    messages,
    draft,
    streamingAnswer,
    streamingSources,
    streamingToolCalls,
    streamingStatus,
    isLoadingSessions,
    isLoadingArchivedSessions,
    isLoadingMessages,
    isStreaming,
    isSending,
    error,
    clearError,
    setDraft,
    sendMessage,
    cancelStreaming,
    loadSessions,
    loadArchivedSessions,
    startSession,
    selectSession,
    deleteSession,
    renameSession,
    pinSession,
    unpinSession,
    archiveSession,
    unarchiveSession,
    editMessage,
    reuseMessage,
    setMessageFeedback,
  };
}
