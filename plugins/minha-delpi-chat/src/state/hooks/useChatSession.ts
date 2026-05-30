import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { flushSync } from "react-dom";

import {
  archiveChatSession,
  createChatSession,
  deleteChatSession,
  listChatMessages,
  listChatSessions,
  upsertChatMessageFeedback,
  pinChatSession,
  renameChatSession,
  switchChatBranch,
  unarchiveChatSession,
  unpinChatSession,
  updateChatMessage,
  uploadChatAttachment,
} from "../../data/api/chatApi";
import type {
  ChatAttachment,
  ChatCanvasOpenPayload,
  ChatMessage,
  ChatSession,
  ChatSource,
  ChatStreamActivityEntry,
  ChatToolCall,
} from "../../data/api/chatTypes";
import {
  isAssistantGenerating,
  sessionAwaitingAssistantResponse,
} from "../chatMessageDelivery";
import { useChatMessagePlayback, type ChatPlaybackPayload } from "./useChatMessagePlayback";
import { useChatStreaming } from "./useChatStreaming";
import { shouldShowRichPresentation, isShortPresentationCaption } from "../../ui/components/chatPresentation";
import {
  clearSessionStreamUi,
  getSessionStreamUi,
  patchSessionStreamUi,
  type SessionStreamUiSnapshot,
} from "../utils/sessionStreamUiCache";
import {
  resolveActivityStatusMessage,
  resolveStreamingHeadline,
  upsertStreamingActivityEntry,
} from "../utils/streamingActivityLog";

type UseChatSessionOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  projectId?: string | null;
  agentId?: string | null;
  onSessionActivated?: (
    sessionId: string,
    context?: { agentId?: string | null; projectId?: string | null },
  ) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
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
  const [pendingUserMessage, setPendingUserMessage] = useState<ChatMessage | null>(
    null,
  );
  const [draft, setDraft] = useState("");
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [streamingSources, setStreamingSources] = useState<ChatSource[]>([]);
  const [streamingToolCalls, setStreamingToolCalls] = useState<ChatToolCall[]>([]);
  const [streamingStatus, setStreamingStatus] = useState<string | null>(null);
  const [streamingActivityLog, setStreamingActivityLog] = useState<ChatStreamActivityEntry[]>(
    [],
  );
  const [streamingShowPresentation, setStreamingShowPresentation] = useState(true);
  const [streamingCanvasOpen, setStreamingCanvasOpen] =
    useState<ChatCanvasOpenPayload | null>(null);
  const [playbackPayload, setPlaybackPayload] = useState<ChatPlaybackPayload | null>(
    null,
  );
  const awaitingPlaybackRef = useRef(false);
  const [lastSentUserText, setLastSentUserText] = useState("");
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingArchivedSessions, setIsLoadingArchivedSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [pendingSessionIds, setPendingSessionIds] = useState<Set<string>>(() => new Set());
  const [error, setError] = useState<string | null>(null);
  const skipNextSessionLoadRef = useRef(false);
  const activeSessionIdRef = useRef<string | null>(null);

  const {
    isSessionStreaming,
    streamMessage,
    resendMessage,
    cancelSessionStreaming,
  } = useChatStreaming({
    getAccessToken: options.getAccessToken,
  });

  const resetStreamingUi = useCallback(() => {
    setStreamingAnswer("");
    setStreamingSources([]);
    setStreamingToolCalls([]);
    setStreamingStatus(null);
    setStreamingActivityLog([]);
    setStreamingShowPresentation(true);
    setStreamingCanvasOpen(null);
    setPlaybackPayload(null);
    awaitingPlaybackRef.current = false;
  }, []);

  const markSessionPending = useCallback((sessionId: string) => {
    setPendingSessionIds((current) => {
      if (current.has(sessionId)) {
        return current;
      }

      const next = new Set(current);
      next.add(sessionId);
      return next;
    });
  }, []);

  const unmarkSessionPending = useCallback((sessionId: string) => {
    setPendingSessionIds((current) => {
      if (!current.has(sessionId)) {
        return current;
      }

      const next = new Set(current);
      next.delete(sessionId);
      return next;
    });
  }, []);

  const isSessionPending = useCallback(
    (sessionId: string) => pendingSessionIds.has(sessionId),
    [pendingSessionIds],
  );

  const isSessionProcessing = useCallback(
    (sessionId: string) =>
      pendingSessionIds.has(sessionId) || isSessionStreaming(sessionId),
    [pendingSessionIds, isSessionStreaming],
  );

  const isActiveSessionBusy = useCallback(() => {
    const sessionId = activeSessionIdRef.current;

    if (!sessionId) {
      return false;
    }

    return isSessionProcessing(sessionId);
  }, [isSessionProcessing]);

  const cancelStreaming = useCallback(() => {
    const sessionId = activeSessionIdRef.current;

    if (sessionId) {
      cancelSessionStreaming(sessionId);
      unmarkSessionPending(sessionId);
      clearSessionStreamUi(sessionId);
    }

    resetStreamingUi();
  }, [cancelSessionStreaming, resetStreamingUi, unmarkSessionPending]);

  const isStreamForActiveSession = useCallback((sessionId: string) => {
    return activeSessionIdRef.current === sessionId;
  }, []);

  const applyStreamUiSnapshot = useCallback((snapshot: SessionStreamUiSnapshot) => {
    setStreamingActivityLog(snapshot.activityLog);
    setStreamingStatus(
      resolveStreamingHeadline(snapshot.status, snapshot.activityLog),
    );
    setStreamingSources(snapshot.sources);
    setStreamingToolCalls(snapshot.toolCalls);
  }, []);

  const restoreStreamUiForSession = useCallback(
    (sessionId: string) => {
      const snapshot = getSessionStreamUi(sessionId);

      if (
        snapshot.activityLog.length === 0 &&
        !snapshot.status &&
        snapshot.sources.length === 0 &&
        snapshot.toolCalls.length === 0
      ) {
        return false;
      }

      applyStreamUiSnapshot(snapshot);
      return true;
    },
    [applyStreamUiSnapshot],
  );

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

  const startSession = useCallback(async () => {
    resetStreamingUi();
    activeSessionIdRef.current = null;
    setError(null);
    setActiveSession(null);
    setMessages([]);
    setPendingUserMessage(null);
    setDraft("");
  }, [resetStreamingUi]);

  const loadMessages = useCallback(
    async (sessionId: string) => {
      setIsLoadingMessages(true);
      setError(null);

      try {
        const data = await listChatMessages(sessionId, {
          getAccessToken: options.getAccessToken,
        });

        if (activeSessionIdRef.current !== sessionId) {
          return;
        }

        setMessages(data);

        const lastUserMessage = [...data]
          .reverse()
          .find((item) => item.role === "user");

        if (lastUserMessage?.content?.trim()) {
          setLastSentUserText("");
        }

        if (sessionAwaitingAssistantResponse(data)) {
          markSessionPending(sessionId);
          restoreStreamUiForSession(sessionId);
        } else {
          unmarkSessionPending(sessionId);
        }
      } catch (err) {
        if (activeSessionIdRef.current !== sessionId) {
          return;
        }

        setError(err instanceof Error ? err.message : "Erro ao carregar mensagens.");
      } finally {
        if (activeSessionIdRef.current === sessionId) {
          setIsLoadingMessages(false);
        }
      }
    },
    [markSessionPending, options.getAccessToken, restoreStreamUiForSession, unmarkSessionPending],
  );

  const selectSession = useCallback(
    (session: ChatSession) => {
      const isSameSession = activeSessionIdRef.current === session.id;
      const sessionStillProcessing = isSessionProcessing(session.id);

      if (!isSameSession) {
        resetStreamingUi();
        setMessages([]);
        setPendingUserMessage(null);
        setError(null);
      }

      activeSessionIdRef.current = session.id;
      setActiveSession(session);

      if (sessionStillProcessing && !restoreStreamUiForSession(session.id)) {
        if (!isSessionStreaming(session.id)) {
          setStreamingStatus("Finalizando resposta em segundo plano...");
        }
      }

      void loadMessages(session.id);
    },
    [isSessionProcessing, isSessionStreaming, loadMessages, resetStreamingUi, restoreStreamUiForSession],
  );

  const finishPlayback = useCallback(() => {
    const sessionId = activeSessionIdRef.current;

    setPlaybackPayload(null);
    awaitingPlaybackRef.current = false;

    if (!sessionId) {
      resetStreamingUi();
      return;
    }

    void loadMessages(sessionId).then(() => {
      if (activeSessionIdRef.current !== sessionId) {
        return;
      }

      setDraft("");
      setPendingUserMessage(null);
      resetStreamingUi();
    });
  }, [loadMessages, resetStreamingUi]);

  const {
    displayedAnswer: playbackAnswer,
    showPresentation: playbackShowPresentation,
    isPlaying: isPlaybackActive,
  } = useChatMessagePlayback(playbackPayload, finishPlayback);

  const streamingAdminDebug = playbackPayload?.adminDebug ?? null;

  useEffect(() => {
    if (!playbackPayload) {
      return;
    }

    setStreamingAnswer(playbackAnswer);
    setStreamingShowPresentation(playbackShowPresentation);
  }, [playbackAnswer, playbackPayload, playbackShowPresentation]);

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

        cancelSessionStreaming(sessionId);
        unmarkSessionPending(sessionId);

        if (activeSession?.id === sessionId) {
          resetStreamingUi();
          activeSessionIdRef.current = null;
          setMessages([]);
        }

        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao excluir conversa.");
        return false;
      }
    },
    [
      activeSession?.id,
      cancelSessionStreaming,
      options.getAccessToken,
      resetStreamingUi,
      sessions,
      unmarkSessionPending,
    ],
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

  const finishSending = useCallback(
    (sessionId: string) => {
      unmarkSessionPending(sessionId);
      clearSessionStreamUi(sessionId);
    },
    [unmarkSessionPending],
  );

  const buildStreamCallbacks = useCallback(
    (sessionForMessage: ChatSession, optimisticUserMessageId?: string | null) => {
      const sessionId = sessionForMessage.id;

      return {
        onUserPersisted: (messageId: string) => {
          if (!isStreamForActiveSession(sessionId) || !optimisticUserMessageId) {
            return;
          }

          setMessages((current) =>
            current.map((item) =>
              item.id === optimisticUserMessageId
                ? {
                    ...item,
                    id: messageId,
                    metadata: {
                      ...(item.metadata ?? {}),
                      optimistic: false,
                    },
                  }
                : item,
            ),
          );
          setPendingUserMessage((current) =>
            current && current.id === optimisticUserMessageId
              ? {
                  ...current,
                  id: messageId,
                  metadata: {
                    ...(current.metadata ?? {}),
                    optimistic: false,
                  },
                }
              : current,
          );
        },
        onStatus: (statusMessage: string) => {
          if (!statusMessage.trim()) {
            return;
          }

          const snapshot = patchSessionStreamUi(sessionId, {
            status: statusMessage.trim(),
          });

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          setStreamingStatus(snapshot.status);
        },
        onActivity: (entry: ChatStreamActivityEntry) => {
          const cached = getSessionStreamUi(sessionId);
          const activityLog = upsertStreamingActivityEntry(cached.activityLog, entry);
          const status = resolveActivityStatusMessage(entry, cached.status);
          const snapshot = patchSessionStreamUi(sessionId, {
            activityLog,
            ...(status ? { status } : {}),
          });

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          flushSync(() => {
            setStreamingActivityLog(snapshot.activityLog);

            if (status) {
              setStreamingStatus(status);
            }
          });
        },
        onSources: (sources: ChatSource[]) => {
          const status =
            sources.length > 0
              ? "Consultando a base de conhecimento..."
              : "Verificando contexto autorizado...";
          const snapshot = patchSessionStreamUi(sessionId, { sources, status });

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          setStreamingSources(snapshot.sources);
          setStreamingStatus(snapshot.status);
        },
        onToolCalls: (toolCalls: ChatToolCall[]) => {
          const hasRichPresentation = shouldShowRichPresentation("", toolCalls);
          const status = hasRichPresentation
            ? "Finalizando apresentação..."
            : toolCalls.length > 0
              ? "Consultando sistemas autorizados..."
              : "Gerando resposta...";
          const snapshot = patchSessionStreamUi(sessionId, { toolCalls, status });

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          setStreamingToolCalls(snapshot.toolCalls);
          setStreamingShowPresentation(hasRichPresentation);
          setStreamingStatus(snapshot.status);
        },
        onAssistantPending: () => {
          const snapshot = patchSessionStreamUi(sessionId, {
            status: "Gerando resposta em linguagem natural...",
          });

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          setStreamingStatus(snapshot.status);
        },
        onPlayback: (payload) => {
          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          awaitingPlaybackRef.current = true;
          setStreamingStatus("Exibindo resposta...");
          setStreamingSources(payload.sources);
          setStreamingToolCalls(payload.toolCalls);
          setStreamingShowPresentation(
            shouldShowRichPresentation(payload.answer, payload.toolCalls),
          );
          setPlaybackPayload(payload);
        },
        onCanvasOpen: (payload) => {
          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          setStreamingCanvasOpen(payload);
          options.onOpenCanvas?.(payload);
        },
        onToken: (token: string) => {
          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          setStreamingShowPresentation(true);
          setStreamingAnswer((current) => current + token);
        },
        onDone: async (response) => {
          finishSending(sessionId);

          try {
            await loadSessions();
          } catch {
            // Lista de sessões é atualização auxiliar; não bloqueia o fluxo.
          }

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          if (response.canvasOpen?.markdown) {
            const canvasPayload: ChatCanvasOpenPayload = {
              title: response.canvasOpen.title,
              markdown: response.canvasOpen.markdown,
              messageId: response.messageId,
              sourceMessageId: response.canvasOpen.sourceMessageId ?? null,
            };

            setStreamingCanvasOpen(canvasPayload);
            options.onOpenCanvas?.(canvasPayload);
          }

          if (response.playback || awaitingPlaybackRef.current) {
            setPlaybackPayload((current) =>
              current ?? {
                messageId: response.messageId,
                answer: response.answer ?? "",
                sources: response.sources ?? [],
                toolCalls: response.toolCalls ?? [],
                adminDebug: response.adminDebug ?? null,
              },
            );
            return;
          }

          const finalAnswer = response.answer ?? "";
          const finalToolCalls = response.toolCalls ?? [];

          if (
            shouldShowRichPresentation(finalAnswer, finalToolCalls) &&
            isShortPresentationCaption(finalAnswer, finalToolCalls)
          ) {
            setPlaybackPayload({
              messageId: response.messageId,
              answer: finalAnswer,
              sources: response.sources ?? [],
              toolCalls: finalToolCalls,
              adminDebug: response.adminDebug ?? null,
            });
            return;
          }

          if (
            shouldShowRichPresentation(
              response.answer ?? "",
              response.toolCalls ?? [],
            ) &&
            !String(response.answer ?? "").trim()
          ) {
            setDraft("");
            setPendingUserMessage(null);
            await loadMessages(sessionId);
            resetStreamingUi();
            return;
          }

          setDraft("");
          setPendingUserMessage(null);
          await loadMessages(sessionId);
          resetStreamingUi();
        },
        onError: (streamError: string) => {
          finishSending(sessionId);

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          setPendingUserMessage(null);
          resetStreamingUi();
          setError(streamError);
        },
      };
    },
    [
      finishSending,
      isStreamForActiveSession,
      loadMessages,
      loadSessions,
      options.onOpenCanvas,
      playbackPayload,
      resetStreamingUi,
    ],
  );

  const editAndResendMessage = useCallback(
    async (messageId: string, content: string) => {
      const normalizedContent = content.trim();

      if (!activeSession) {
        setError("Selecione uma conversa.");
        return null;
      }

      if (!normalizedContent) {
        setError("Informe uma mensagem.");
        return null;
      }

      if (isActiveSessionBusy()) {
        setError("Aguarde a resposta atual terminar.");
        return null;
      }

      const messageIndex = messages.findIndex((message) => message.id === messageId);

      if (messageIndex < 0) {
        setError("Mensagem não encontrada.");
        return null;
      }

      const targetMessage = messages[messageIndex];

      if (targetMessage.role !== "user" || targetMessage.id.startsWith("optimistic-")) {
        setError("Somente perguntas do usuário podem ser reenviadas.");
        return null;
      }

      setError(null);
      markSessionPending(activeSession.id);
      clearSessionStreamUi(activeSession.id);
      patchSessionStreamUi(activeSession.id, {
        activityLog: [],
        status: "Preparando novo envio...",
        sources: [],
        toolCalls: [],
      });
      setStreamingAnswer("");
      setStreamingSources([]);
      setStreamingToolCalls([]);
      setStreamingActivityLog([]);
      setStreamingStatus("Preparando novo envio...");

      setMessages((current) =>
        current
          .slice(0, messageIndex + 1)
          .map((message, index) =>
            index === messageIndex
              ? {
                  ...message,
                  content: normalizedContent,
                  metadata: {
                    ...message.metadata,
                    edited: true,
                  },
                }
              : message,
          ),
      );

      try {
        await resendMessage({
          sessionId: activeSession.id,
          messageId,
          content: normalizedContent,
          context: activeSession.context ?? "geral",
          ...buildStreamCallbacks(activeSession),
        });

        return {
          id: messageId,
          session_id: activeSession.id,
          role: "user" as const,
          content: normalizedContent,
          metadata: targetMessage.metadata,
          created_at: targetMessage.created_at,
        };
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          finishSending(activeSession.id);
          return null;
        }

        setStreamingStatus(null);
        setError(err instanceof Error ? err.message : "Erro ao reenviar mensagem.");
        finishSending(activeSession.id);
        await loadMessages(activeSession.id);
        return null;
      }
    },
    [
      activeSession,
      buildStreamCallbacks,
      finishSending,
      isActiveSessionBusy,
      loadMessages,
      markSessionPending,
      messages,
      resendMessage,
    ],
  );

  const sendMessage = useCallback(async (params: { attachments?: File[]; content?: string } = {}) => {
    const message = (params.content ?? draft).trim();
    const fromDraft = params.content == null;

    if (!message || isActiveSessionBusy()) {
      return;
    }

    setLastSentUserText(message);
    const optimisticId = `optimistic-${Date.now()}`;
    let sessionForMessage = activeSession;

    setError(null);
    if (fromDraft) {
      setDraft("");
    }
    setStreamingAnswer("");
    setStreamingSources([]);
    setStreamingToolCalls([]);
    setStreamingActivityLog([]);
    setStreamingShowPresentation(false);
    const initialStatus = activeSession
      ? "Preparando sua pergunta..."
      : "Criando conversa e preparando sua pergunta...";
    setStreamingStatus(initialStatus);

    if (activeSession) {
      clearSessionStreamUi(activeSession.id);
      patchSessionStreamUi(activeSession.id, {
        activityLog: [],
        status: initialStatus,
        sources: [],
        toolCalls: [],
      });
      markSessionPending(activeSession.id);
    }

    const optimisticMessage: ChatMessage = {
      ...createOptimisticUserMessage(
        sessionForMessage?.id ?? "pending",
        message,
      ),
      id: optimisticId,
    };

    setPendingUserMessage(optimisticMessage);
    setMessages((current) => [...current, optimisticMessage]);

    try {
      if (!sessionForMessage) {
        sessionForMessage = await createChatSession(
          {
            title: "Nova conversa",
            context: "geral",
            projectId: options.projectId ?? null,
            agentId: options.agentId ?? null,
          },
          {
            getAccessToken: options.getAccessToken,
          },
        );

        skipNextSessionLoadRef.current = true;
        activeSessionIdRef.current = sessionForMessage!.id;
        markSessionPending(sessionForMessage!.id);
        clearSessionStreamUi(sessionForMessage!.id);
        patchSessionStreamUi(sessionForMessage!.id, {
          activityLog: [],
          status: initialStatus,
          sources: [],
          toolCalls: [],
        });
        setSessions((current) => [sessionForMessage!, ...current]);
        setActiveSession(sessionForMessage);
        queueMicrotask(() => {
          options.onSessionActivated?.(sessionForMessage!.id, {
            agentId: sessionForMessage!.agent_id ?? options.agentId ?? null,
            projectId: sessionForMessage!.project_id ?? options.projectId ?? null,
          });
        });
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

      markSessionPending(sessionForMessage.id);

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
        agentId: options.agentId,
        ...buildStreamCallbacks(sessionForMessage, optimisticId),
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        if (sessionForMessage) {
          finishSending(sessionForMessage.id);
        }
        return;
      }

      setStreamingStatus(null);
      setPendingUserMessage(null);
      setError(err instanceof Error ? err.message : "Erro ao enviar mensagem.");
      if (sessionForMessage) {
        finishSending(sessionForMessage.id);
      }
    }
  }, [
    activeSession,
    draft,
    finishSending,
    isActiveSessionBusy,
    loadMessages,
    loadSessions,
    markSessionPending,
    options.agentId,
    options.getAccessToken,
    options.projectId,
    streamMessage,
    buildStreamCallbacks,
  ]);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    activeSessionIdRef.current = activeSession?.id ?? null;
  }, [activeSession]);

  useEffect(() => {
    if (!activeSession) {
      return;
    }

    if (skipNextSessionLoadRef.current) {
      skipNextSessionLoadRef.current = false;
      return;
    }

    if (
      (isSessionPending(activeSession.id) ||
        isSessionStreaming(activeSession.id) ||
        pendingUserMessage) &&
      messages.length > 0
    ) {
      return;
    }

    void loadMessages(activeSession.id);
  }, [
    activeSession,
    isSessionPending,
    isSessionStreaming,
    loadMessages,
    messages.length,
    pendingUserMessage,
  ]);

  useEffect(() => {
    const sessionId = activeSession?.id;

    if (!sessionId || isSessionStreaming(sessionId) || playbackPayload) {
      return;
    }

    const awaitingBackground =
      (isSessionPending(sessionId) && !pendingUserMessage) ||
      sessionAwaitingAssistantResponse(messages);

    if (!awaitingBackground) {
      setStreamingStatus((current) =>
        current === "Finalizando resposta em segundo plano..." ? null : current,
      );
      return;
    }

    if (!restoreStreamUiForSession(sessionId)) {
      setStreamingStatus("Finalizando resposta em segundo plano...");
    }

    const interval = window.setInterval(() => {
      void loadMessages(sessionId);
    }, 2500);

    return () => {
      window.clearInterval(interval);
    };
  }, [
    activeSession?.id,
    isSessionPending,
    isSessionStreaming,
    loadMessages,
    messages,
    pendingUserMessage,
    playbackPayload,
    restoreStreamUiForSession,
  ]);

  const visibleMessages = useMemo(() => {
    let list = messages;

    const hideGeneratingPlaceholder =
      Boolean(activeSession) &&
      (isSessionStreaming(activeSession.id) ||
        isSessionPending(activeSession.id) ||
        playbackPayload) &&
      list.length > 0 &&
      isAssistantGenerating(list[list.length - 1]);

    if (hideGeneratingPlaceholder) {
      list = list.slice(0, -1);
    }

    if (!pendingUserMessage) {
      return list;
    }

    if (list.some((message) => message.id === pendingUserMessage.id)) {
      return list;
    }

    return [...list, pendingUserMessage];
  }, [activeSession, isSessionPending, isSessionStreaming, messages, pendingUserMessage, playbackPayload]);

  const isComposerBusy = isActiveSessionBusy();
  const isStreamingActiveSession =
    Boolean(activeSession) &&
    (isSessionStreaming(activeSession.id) ||
      isSessionPending(activeSession.id) ||
      isPlaybackActive);

  const switchMessageBranch = useCallback(
    async (anchorUserMessageId: string) => {
      const sessionId = activeSession?.id;

      if (!sessionId || isActiveSessionBusy()) {
        return;
      }

      setError(null);

      try {
        const data = await switchChatBranch(sessionId, anchorUserMessageId, {
          getAccessToken: options.getAccessToken,
        });

        if (activeSessionIdRef.current !== sessionId) {
          return;
        }

        setMessages(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao alternar variação.");
      }
    },
    [activeSession?.id, isActiveSessionBusy, options.getAccessToken],
  );

  const continueFromMessage = useCallback(
    async (messageId: string) => {
      if (!activeSession || isActiveSessionBusy()) {
        return;
      }

      setError(null);

      try {
        const newSession = await createChatSession(
          {
            title: activeSession.title
              ? `${activeSession.title} (continuação)`
              : "Continuação",
            context: activeSession.context ?? "geral",
            projectId: activeSession.project_id,
            agentId: activeSession.agent_id,
            forkFromSessionId: activeSession.id,
            forkUntilMessageId: messageId,
          },
          { getAccessToken: options.getAccessToken },
        );

        setSessions((current) => [newSession, ...current]);
        selectSession(newSession);
        options.onSessionActivated?.(newSession.id, {
          agentId: newSession.agent_id ?? options.agentId ?? null,
          projectId: newSession.project_id ?? options.projectId ?? null,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao continuar conversa.");
      }
    },
    [
      activeSession,
      isActiveSessionBusy,
      options,
      selectSession,
    ],
  );

  return {
    sessions,
    archivedSessions,
    activeSession,
    messages: visibleMessages,
    draft,
    streamingAnswer,
    streamingSources,
    streamingToolCalls,
    streamingAdminDebug,
    streamingStatus,
    streamingActivityLog,
    streamingShowPresentation,
    streamingCanvasOpen,
    lastSentUserText,
    isLoadingSessions,
    isLoadingArchivedSessions,
    isLoadingMessages,
    isComposerBusy,
    isStreamingActiveSession,
    isPlaybackActive,
    isSessionProcessing,
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
    editAndResendMessage,
    reuseMessage,
    setMessageFeedback,
    switchMessageBranch,
    continueFromMessage,
  };
}
