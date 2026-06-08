import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { flushSync } from "react-dom";

import {
  archiveChatSession,
  cancelChatStream,
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
  ChatResponseModeId,
  ChatSession,
  ChatSource,
  ChatStreamActivityEntry,
  ChatToolCall,
} from "../../data/api/chatTypes";
import {
  isAssistantGenerating,
  sanitizeMessagesAfterStreamDismiss,
  sessionAwaitingAssistantResponse,
  shouldAppendPendingUserMessage,
} from "../chatMessageDelivery";
import { isIncompleteChatStreamError } from "../chatStreamConnection";
import {
  applyStreamHandoffToMessages,
  handoffFromPlaybackPayload,
  streamContentAlreadyDisplayed,
  type AssistantTurnHandoff,
} from "../chatStreamHandoff";
import { useChatMessagePlayback, type ChatPlaybackPayload } from "./useChatMessagePlayback";
import { useChatStreaming } from "./useChatStreaming";
import { shouldShowRichPresentation, isShortPresentationCaption } from "../../ui/components/chatPresentation";
import { hasUnresolvedShortcutPlaceholders } from "../../ui/chatShortcutPrompt";
import {
  clearSessionStreamUi,
  getSessionStreamUi,
  patchSessionStreamUi,
  type SessionStreamUiSnapshot,
} from "../utils/sessionStreamUiCache";
import {
  appendStatusToActivityLog,
  resolveActivityStatusMessage,
  resolveStreamingHeadline,
  upsertStreamingActivityEntry,
} from "../utils/streamingActivityLog";

type UseChatSessionOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  projectId?: string | null;
  agentId?: string | null;
  chatMode?: "common" | "agent";
  onSessionActivated?: (
    sessionId: string,
    context?: { agentId?: string | null; projectId?: string | null },
  ) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
  /** Abre o diálogo de preenchimento quando a mensagem ainda tem `{{placeholders}}`. */
  onShortcutPromptRequired?: (template: string) => void;
  /** Evita reabrir o diálogo enquanto o usuário já está preenchendo. */
  isShortcutPromptOpen?: () => boolean;
  /** Modo de resposta LLM (rápida / normal / pensador) escolhido no composer. */
  getResponseMode?: () => ChatResponseModeId;
};

function isPersistedChatMessageId(messageId: string): boolean {
  return !messageId.startsWith("optimistic-") && /^[0-9a-f-]{36}$/i.test(messageId);
}

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
  const onShortcutPromptRequiredRef = useRef(options.onShortcutPromptRequired);
  onShortcutPromptRequiredRef.current = options.onShortcutPromptRequired;
  const getResponseModeRef = useRef(options.getResponseMode);
  getResponseModeRef.current = options.getResponseMode;
  const isShortcutPromptOpenRef = useRef(options.isShortcutPromptOpen);
  isShortcutPromptOpenRef.current = options.isShortcutPromptOpen;

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
  const streamingAnswerRef = useRef("");
  const streamingToolCallsRef = useRef<ChatToolCall[]>([]);
  const playbackPayloadRef = useRef<ChatPlaybackPayload | null>(null);
  const [lastSentUserText, setLastSentUserText] = useState("");
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingArchivedSessions, setIsLoadingArchivedSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [pendingSessionIds, setPendingSessionIds] = useState<Set<string>>(() => new Set());
  const [cancellingSessionIds, setCancellingSessionIds] = useState<Set<string>>(() => new Set());
  const [error, setError] = useState<string | null>(null);
  const [branchSwitchingMessageId, setBranchSwitchingMessageId] = useState<string | null>(
    null,
  );
  const skipNextSessionLoadRef = useRef(false);
  const activeSessionIdRef = useRef<string | null>(null);
  const userDismissedBackgroundStreamRef = useRef<Set<string>>(new Set());
  const [dismissedStreamRevision, setDismissedStreamRevision] = useState(0);

  const isSessionStreamDismissed = useCallback(
    (sessionId: string) => userDismissedBackgroundStreamRef.current.has(sessionId),
    [dismissedStreamRevision],
  );

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
    playbackPayloadRef.current = null;
    streamingAnswerRef.current = "";
    streamingToolCallsRef.current = [];
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

  const markSessionCancelling = useCallback((sessionId: string) => {
    setCancellingSessionIds((current) => {
      if (current.has(sessionId)) {
        return current;
      }

      const next = new Set(current);
      next.add(sessionId);
      return next;
    });
  }, []);

  const unmarkSessionCancelling = useCallback((sessionId: string) => {
    setCancellingSessionIds((current) => {
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
      pendingSessionIds.has(sessionId) ||
      isSessionStreaming(sessionId) ||
      cancellingSessionIds.has(sessionId),
    [cancellingSessionIds, pendingSessionIds, isSessionStreaming],
  );

  const isActiveSessionBusy = useCallback(() => {
    const sessionId = activeSessionIdRef.current;

    if (!sessionId) {
      return false;
    }

    return isSessionProcessing(sessionId);
  }, [isSessionProcessing]);

  const isStreamForActiveSession = useCallback((sessionId: string) => {
    return activeSessionIdRef.current === sessionId;
  }, []);

  const applyStreamUiSnapshot = useCallback((snapshot: SessionStreamUiSnapshot) => {
    setStreamingActivityLog(snapshot.activityLog);
    setStreamingStatus(
      resolveStreamingHeadline(snapshot.status, snapshot.activityLog),
    );
    setStreamingSources(snapshot.sources);
    setStreamingToolCalls(snapshot.toolCalls ?? []);
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

  const patchStreamStatus = useCallback((sessionId: string, status: string) => {
    const trimmed = status.trim();

    if (!trimmed) {
      return getSessionStreamUi(sessionId);
    }

    const cached = getSessionStreamUi(sessionId);

    return patchSessionStreamUi(sessionId, {
      status: trimmed,
      activityLog: appendStatusToActivityLog(cached.activityLog, trimmed),
    });
  }, []);

  const ensureAwaitingStreamUi = useCallback(
    (sessionId: string) => {
      if (restoreStreamUiForSession(sessionId)) {
        return;
      }

      const fallbackStatus = "Processando sua solicitação...";
      const snapshot = patchSessionStreamUi(sessionId, {
        activityLog: appendStatusToActivityLog([], fallbackStatus),
        status: fallbackStatus,
      });

      if (isStreamForActiveSession(sessionId)) {
        applyStreamUiSnapshot(snapshot);
      }
    },
    [applyStreamUiSnapshot, isStreamForActiveSession, restoreStreamUiForSession],
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
    async (
      sessionId: string,
      loadOptions?: {
        userDismissedBackground?: boolean;
        background?: boolean;
      },
    ) => {
      const background = loadOptions?.background === true;

      if (!background) {
        setIsLoadingMessages(true);
      }

      setError(null);

      try {
        let data = await listChatMessages(sessionId, {
          getAccessToken: options.getAccessToken,
        });

        if (activeSessionIdRef.current !== sessionId) {
          return;
        }

        const userDismissed =
          loadOptions?.userDismissedBackground ||
          userDismissedBackgroundStreamRef.current.has(sessionId);

        if (userDismissed) {
          data = sanitizeMessagesAfterStreamDismiss(data);
        } else if (!userDismissedBackgroundStreamRef.current.has(sessionId)) {
          const serverStillAwaiting = sessionAwaitingAssistantResponse(data);

          if (serverStillAwaiting) {
            markSessionPending(sessionId);
            ensureAwaitingStreamUi(sessionId);
          } else {
            unmarkSessionPending(sessionId);
            clearSessionStreamUi(sessionId);

            if (activeSessionIdRef.current === sessionId) {
              resetStreamingUi();
            }
          }
        }

        setMessages(data);

        const lastUserMessage = [...data]
          .reverse()
          .find((item) => item.role === "user");

        if (lastUserMessage?.content?.trim()) {
          setLastSentUserText("");
        }

        const keepDismissedUi =
          userDismissed || userDismissedBackgroundStreamRef.current.has(sessionId);

        if (keepDismissedUi) {
          unmarkSessionPending(sessionId);
          unmarkSessionCancelling(sessionId);

          if (activeSessionIdRef.current === sessionId) {
            resetStreamingUi();
          }
        }
      } catch (err) {
        if (activeSessionIdRef.current !== sessionId) {
          return;
        }

        setError(err instanceof Error ? err.message : "Erro ao carregar mensagens.");
      } finally {
        if (activeSessionIdRef.current === sessionId && !background) {
          setIsLoadingMessages(false);
        }
      }
    },
    [
      ensureAwaitingStreamUi,
      markSessionPending,
      options.getAccessToken,
      resetStreamingUi,
      unmarkSessionCancelling,
      unmarkSessionPending,
    ],
  );

  const finalizeAssistantTurn = useCallback(
    (sessionId: string, handoff: AssistantTurnHandoff) => {
      clearSessionStreamUi(sessionId);
      setMessages((current) => applyStreamHandoffToMessages(current, handoff));
      setPlaybackPayload(null);
      playbackPayloadRef.current = null;
      awaitingPlaybackRef.current = false;
      setDraft("");
      setPendingUserMessage(null);
      resetStreamingUi();
      streamingAnswerRef.current = "";
      streamingToolCallsRef.current = [];

      void loadMessages(sessionId, { background: true });
    },
    [loadMessages, resetStreamingUi],
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

      if (
        sessionStillProcessing &&
        !userDismissedBackgroundStreamRef.current.has(session.id) &&
        !isSessionStreaming(session.id)
      ) {
        ensureAwaitingStreamUi(session.id);
      }

      void loadMessages(session.id);
    },
    [
      ensureAwaitingStreamUi,
      isSessionProcessing,
      isSessionStreaming,
      loadMessages,
      resetStreamingUi,
    ],
  );

  const finishPlayback = useCallback(() => {
    const sessionId = activeSessionIdRef.current;
    const payload = playbackPayloadRef.current;

    if (!sessionId || !payload) {
      resetStreamingUi();
      return;
    }

    finalizeAssistantTurn(sessionId, handoffFromPlaybackPayload(sessionId, payload));
  }, [finalizeAssistantTurn, resetStreamingUi]);

  const {
    displayedAnswer: playbackAnswer,
    showPresentation: playbackShowPresentation,
    isPlaying: isPlaybackActive,
  } = useChatMessagePlayback(playbackPayload, finishPlayback);

  const streamingAdminDebug = playbackPayload?.adminDebug ?? null;

  useEffect(() => {
    playbackPayloadRef.current = playbackPayload;
  }, [playbackPayload]);

  useEffect(() => {
    streamingAnswerRef.current = streamingAnswer;
  }, [streamingAnswer]);

  useEffect(() => {
    streamingToolCallsRef.current = streamingToolCalls;
  }, [streamingToolCalls]);

  useEffect(() => {
    if (!playbackPayload) {
      return;
    }

    setStreamingAnswer(playbackAnswer);
    streamingAnswerRef.current = playbackAnswer;
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
    async (
      messageId: string,
      rating: -1 | 1 | null,
      reason?: string | null,
    ): Promise<{
      thanksMessage?: string;
      correctiveActions?: Array<{
        id: string;
        label: string;
        action: string;
        query?: string;
      }>;
    } | void> => {
      if (!activeSession) {
        return;
      }

      const result = await upsertChatMessageFeedback(
        activeSession.id,
        messageId,
        rating,
        {
          getAccessToken: options.getAccessToken,
        },
        reason,
      );

      setMessages((current) =>
        current.map((message) =>
          message.id === messageId
            ? {
                ...message,
                user_feedback: rating,
                user_feedback_reason:
                  rating === -1 && reason
                    ? reason
                    : rating === null
                      ? null
                      : message.user_feedback_reason,
              }
            : message,
        ),
      );

      if (result && "thanksMessage" in result && result.thanksMessage) {
        return { thanksMessage: result.thanksMessage };
      }

      if (result && "correctiveActions" in result && result.correctiveActions?.length) {
        return { correctiveActions: result.correctiveActions };
      }
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
    },
    [unmarkSessionPending],
  );

  const dismissBackgroundStream = useCallback(
    (sessionId: string) => {
      userDismissedBackgroundStreamRef.current.add(sessionId);
      setDismissedStreamRevision((current) => current + 1);
      unmarkSessionPending(sessionId);
      cancelSessionStreaming(sessionId);
      clearSessionStreamUi(sessionId);

      void cancelChatStream(sessionId, {
        getAccessToken: options.getAccessToken,
      }).catch(() => undefined);
    },
    [cancelSessionStreaming, options.getAccessToken, unmarkSessionPending],
  );

  const cancelStreaming = useCallback(() => {
    const sessionId = activeSessionIdRef.current;

    if (sessionId) {
      markSessionCancelling(sessionId);
      dismissBackgroundStream(sessionId);
      resetStreamingUi();

      setMessages((current) =>
        sanitizeMessagesAfterStreamDismiss(
          current.filter((message) => !message.metadata?.optimistic),
        ),
      );

      void loadMessages(sessionId, { userDismissedBackground: true }).finally(() => {
        unmarkSessionCancelling(sessionId);
      });
    } else {
      resetStreamingUi();
    }

    setPendingUserMessage(null);

    const textToRestore = lastSentUserText.trim();

    if (textToRestore) {
      setDraft(textToRestore);
    } else {
      setDraft("");
    }
  }, [
    dismissBackgroundStream,
    lastSentUserText,
    loadMessages,
    markSessionCancelling,
    resetStreamingUi,
    unmarkSessionCancelling,
  ]);

  const buildStreamCallbacks = useCallback(
    (
      sessionForMessage: ChatSession,
      optimisticUserMessageId?: string | null,
      streamOptions?: { refreshOnUserPersisted?: boolean },
    ) => {
      const sessionId = sessionForMessage.id;
      const shouldIgnoreStreamEvent = () =>
        userDismissedBackgroundStreamRef.current.has(sessionId);

      return {
        onUserPersisted: (messageId: string) => {
          if (shouldIgnoreStreamEvent()) {
            return;
          }

          if (!isStreamForActiveSession(sessionId) || !optimisticUserMessageId) {
            if (streamOptions?.refreshOnUserPersisted && isStreamForActiveSession(sessionId)) {
              void loadMessages(sessionId);
            }
            return;
          }

          flushSync(() => {
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
          });

          if (streamOptions?.refreshOnUserPersisted) {
            void loadMessages(sessionId);
          }
        },
        onStatus: (statusMessage: string) => {
          if (shouldIgnoreStreamEvent() || !statusMessage.trim()) {
            return;
          }

          const snapshot = patchStreamStatus(sessionId, statusMessage);

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          flushSync(() => {
            setStreamingActivityLog(snapshot.activityLog);
            setStreamingStatus(
              resolveStreamingHeadline(snapshot.status, snapshot.activityLog),
            );
          });
        },
        onActivity: (entry: ChatStreamActivityEntry) => {
          if (shouldIgnoreStreamEvent()) {
            return;
          }

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
          if (shouldIgnoreStreamEvent()) {
            return;
          }

          const status =
            sources.length > 0
              ? "Consultando a base de conhecimento..."
              : "Verificando contexto autorizado...";
          patchStreamStatus(sessionId, status);
          const snapshot = patchSessionStreamUi(sessionId, { sources });

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          setStreamingSources(snapshot.sources);
          setStreamingActivityLog(snapshot.activityLog);
          setStreamingStatus(
            resolveStreamingHeadline(snapshot.status, snapshot.activityLog),
          );
        },
        onToolCalls: (toolCalls: ChatToolCall[]) => {
          if (shouldIgnoreStreamEvent()) {
            return;
          }

          const hasRichPresentation = shouldShowRichPresentation("", toolCalls);
          const status = hasRichPresentation
            ? "Finalizando apresentação..."
            : toolCalls.length > 0
              ? "Consultando sistemas autorizados..."
              : "Gerando resposta...";
          patchStreamStatus(sessionId, status);
          const snapshot = patchSessionStreamUi(sessionId, { toolCalls });

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          const streamToolCalls = snapshot.toolCalls ?? [];
          setStreamingToolCalls(streamToolCalls);
          streamingToolCallsRef.current = streamToolCalls;
          setStreamingShowPresentation(hasRichPresentation);
          setStreamingActivityLog(snapshot.activityLog);
          setStreamingStatus(
            resolveStreamingHeadline(snapshot.status, snapshot.activityLog),
          );
        },
        onAssistantPending: () => {
          if (shouldIgnoreStreamEvent()) {
            return;
          }

          const snapshot = patchStreamStatus(
            sessionId,
            "Gerando resposta em linguagem natural...",
          );

          if (!isStreamForActiveSession(sessionId)) {
            return;
          }

          setStreamingActivityLog(snapshot.activityLog);
          setStreamingStatus(
            resolveStreamingHeadline(snapshot.status, snapshot.activityLog),
          );
        },
        onPlayback: (payload) => {
          if (shouldIgnoreStreamEvent() || !isStreamForActiveSession(sessionId)) {
            return;
          }

          awaitingPlaybackRef.current = true;
          setStreamingStatus("Exibindo resposta...");
          setStreamingSources(payload.sources);
          const playbackToolCalls = payload.toolCalls ?? [];
          setStreamingToolCalls(playbackToolCalls);
          streamingToolCallsRef.current = playbackToolCalls;
          setStreamingShowPresentation(
            shouldShowRichPresentation(payload.answer, payload.toolCalls),
          );
          const skipReveal = streamContentAlreadyDisplayed(
            streamingAnswerRef.current,
            streamingToolCallsRef.current,
            payload,
          );
          const enriched: ChatPlaybackPayload = { ...payload, skipReveal };
          playbackPayloadRef.current = enriched;
          setPlaybackPayload(enriched);
        },
        onCanvasOpen: (payload) => {
          if (shouldIgnoreStreamEvent() || !isStreamForActiveSession(sessionId)) {
            return;
          }

          setStreamingCanvasOpen(payload);
          options.onOpenCanvas?.(payload);
        },
        onToken: (token: string) => {
          if (shouldIgnoreStreamEvent() || !isStreamForActiveSession(sessionId)) {
            return;
          }

          setStreamingShowPresentation(true);
          setStreamingAnswer((current) => {
            const next = current + token;
            streamingAnswerRef.current = next;
            return next;
          });
        },
        onDone: async (response) => {
          finishSending(sessionId);

          if (shouldIgnoreStreamEvent()) {
            return;
          }

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

          const finalAnswer = response.answer ?? "";
          const finalToolCalls = response.toolCalls ?? [];
          const turnHandoff: AssistantTurnHandoff = {
            messageId: response.messageId,
            sessionId,
            answer: finalAnswer,
            sources: response.sources ?? [],
            toolCalls: finalToolCalls,
            adminDebug: response.adminDebug ?? null,
          };

          if (response.playback || awaitingPlaybackRef.current) {
            const existingPayload = playbackPayloadRef.current;

            if (existingPayload) {
              if (
                streamContentAlreadyDisplayed(
                  streamingAnswerRef.current,
                  streamingToolCallsRef.current,
                  existingPayload,
                )
              ) {
                finalizeAssistantTurn(
                  sessionId,
                  handoffFromPlaybackPayload(sessionId, existingPayload),
                );
              }

              return;
            }

            const payload: ChatPlaybackPayload = {
              messageId: response.messageId,
              answer: finalAnswer,
              sources: turnHandoff.sources,
              toolCalls: finalToolCalls,
              adminDebug: response.adminDebug ?? null,
              skipReveal: streamContentAlreadyDisplayed(
                streamingAnswerRef.current,
                streamingToolCallsRef.current,
                {
                  answer: finalAnswer,
                  toolCalls: finalToolCalls,
                },
              ),
            };

            if (payload.skipReveal) {
              finalizeAssistantTurn(sessionId, handoffFromPlaybackPayload(sessionId, payload));
              return;
            }

            playbackPayloadRef.current = payload;
            setPlaybackPayload(payload);
            return;
          }

          if (
            shouldShowRichPresentation(finalAnswer, finalToolCalls) &&
            isShortPresentationCaption(finalAnswer, finalToolCalls)
          ) {
            const captionPayload: ChatPlaybackPayload = {
              messageId: response.messageId,
              answer: finalAnswer,
              sources: turnHandoff.sources,
              toolCalls: finalToolCalls,
              adminDebug: response.adminDebug ?? null,
              skipReveal: streamContentAlreadyDisplayed(
                streamingAnswerRef.current,
                streamingToolCallsRef.current,
                {
                  answer: finalAnswer,
                  toolCalls: finalToolCalls,
                },
              ),
            };

            if (captionPayload.skipReveal) {
              finalizeAssistantTurn(
                sessionId,
                handoffFromPlaybackPayload(sessionId, captionPayload),
              );
              return;
            }

            playbackPayloadRef.current = captionPayload;
            setPlaybackPayload(captionPayload);
            return;
          }

          if (
            shouldShowRichPresentation(finalAnswer, finalToolCalls) &&
            !finalAnswer.trim()
          ) {
            finalizeAssistantTurn(sessionId, turnHandoff);
            return;
          }

          finalizeAssistantTurn(sessionId, turnHandoff);
        },
        onError: (streamError: string) => {
          finishSending(sessionId);

          if (shouldIgnoreStreamEvent() || !isStreamForActiveSession(sessionId)) {
            return;
          }

          if (isIncompleteChatStreamError(streamError)) {
            markSessionPending(sessionId);
            ensureAwaitingStreamUi(sessionId);
            setPendingUserMessage(null);
            void loadMessages(sessionId);
            return;
          }

          dismissBackgroundStream(sessionId);
          setPendingUserMessage(null);
          resetStreamingUi();
          setMessages((current) =>
            sanitizeMessagesAfterStreamDismiss(
              current.filter((message) => !message.metadata?.optimistic),
            ),
          );
          void loadMessages(sessionId, { userDismissedBackground: true });
          setError(streamError);
        },
      };
    },
    [
      dismissBackgroundStream,
      ensureAwaitingStreamUi,
      finalizeAssistantTurn,
      finishSending,
      isStreamForActiveSession,
      loadMessages,
      loadSessions,
      markSessionPending,
      options.onOpenCanvas,
      patchStreamStatus,
      resetStreamingUi,
    ],
  );

  const sendMessage = useCallback(async (params: {
    attachments?: File[];
    attachmentIds?: string[];
    attachmentPreview?: {
      id: string;
      original_filename: string;
      size_bytes: number;
      content_type: string | null;
      status: string;
      parsed?: boolean;
      readingStatus?: string;
    }[];
    content?: string;
    /** Sessão alvo (ex.: logo após fork) quando o state ainda não atualizou. */
    session?: ChatSession;
  } = {}) => {
    const message = (params.content ?? draft).trim();
    const fromDraft = params.content == null;

    if (!message || isActiveSessionBusy()) {
      return;
    }

    if (hasUnresolvedShortcutPlaceholders(message)) {
      if (isShortcutPromptOpenRef.current?.()) {
        return;
      }

      if (fromDraft) {
        setDraft(message);
      }

      if (onShortcutPromptRequiredRef.current) {
        onShortcutPromptRequiredRef.current(message);
        return;
      }

      setError(
        "Preencha o código ou os campos da pergunta no diálogo dos atalhos antes de enviar.",
      );
      return;
    }

    setLastSentUserText(message);
    const optimisticId = `optimistic-${Date.now()}`;
    let sessionForMessage = params.session ?? activeSession;

    setError(null);
    if (fromDraft) {
      setDraft("");
    }
    setStreamingAnswer("");
    setStreamingSources([]);
    setStreamingToolCalls([]);
    setStreamingShowPresentation(false);
    const initialStatus = sessionForMessage
      ? "Preparando sua pergunta..."
      : "Criando conversa e preparando sua pergunta...";
    const initialActivityLog = appendStatusToActivityLog([], initialStatus);
    setStreamingActivityLog(initialActivityLog);
    setStreamingStatus(
      resolveStreamingHeadline(initialStatus, initialActivityLog),
    );

    if (sessionForMessage) {
      userDismissedBackgroundStreamRef.current.delete(sessionForMessage.id);
      clearSessionStreamUi(sessionForMessage.id);
      patchSessionStreamUi(sessionForMessage.id, {
        activityLog: initialActivityLog,
        status: initialStatus,
        sources: [],
        toolCalls: [],
      });
      markSessionPending(sessionForMessage.id);
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
          activityLog: initialActivityLog,
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
      const presetAttachmentIds = (params.attachmentIds ?? []).filter(Boolean);

      if (presetAttachmentIds.length === 0) {
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
      }

      const attachmentIds =
        presetAttachmentIds.length > 0
          ? presetAttachmentIds
          : uploadedAttachments.map((attachment) => attachment.id);

      const attachmentPreview =
        params.attachmentPreview ??
        uploadedAttachments.map((attachment) => {
          const indexed =
            attachment.status === "indexed" ||
            Boolean(
              attachment.metadata &&
                typeof attachment.metadata === "object" &&
                (attachment.metadata as Record<string, unknown>).indexed,
            );

          const metadata = attachment.metadata as Record<string, unknown> | null;
          const readingStatus =
            typeof metadata?.readingStatus === "string" ? metadata.readingStatus : undefined;

          return {
            id: attachment.id,
            original_filename: attachment.original_filename,
            size_bytes: attachment.size_bytes,
            content_type: attachment.content_type,
            status: attachment.status,
            parsed: indexed,
            readingStatus,
          };
        });

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
        chatMode: options.chatMode ?? (options.agentId ? "agent" : "common"),
        responseMode: getResponseModeRef.current?.() ?? "normal",
        ...buildStreamCallbacks(sessionForMessage, optimisticId),
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        if (
          sessionForMessage?.id &&
          userDismissedBackgroundStreamRef.current.has(sessionForMessage.id)
        ) {
          return;
        }

        if (sessionForMessage) {
          markSessionCancelling(sessionForMessage.id);
          dismissBackgroundStream(sessionForMessage.id);
          resetStreamingUi();

          setMessages((current) =>
            sanitizeMessagesAfterStreamDismiss(
              current.filter((message) => !message.metadata?.optimistic),
            ),
          );

          void loadMessages(sessionForMessage.id, { userDismissedBackground: true }).finally(
            () => {
              unmarkSessionCancelling(sessionForMessage.id);
            },
          );
        } else {
          resetStreamingUi();
        }

        setPendingUserMessage(null);

        const textToRestore = lastSentUserText.trim();

        if (textToRestore) {
          setDraft(textToRestore);
        }

        return;
      }

      if (sessionForMessage && isIncompleteChatStreamError(err)) {
        markSessionPending(sessionForMessage.id);
        ensureAwaitingStreamUi(sessionForMessage.id);
        setPendingUserMessage(null);
        void loadMessages(sessionForMessage.id);
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
    dismissBackgroundStream,
    ensureAwaitingStreamUi,
    finishSending,
    isActiveSessionBusy,
    lastSentUserText,
    loadMessages,
    loadSessions,
    markSessionCancelling,
    markSessionPending,
    options.agentId,
    options.chatMode,
    options.getAccessToken,
    options.projectId,
    resetStreamingUi,
    streamMessage,
    buildStreamCallbacks,
    unmarkSessionCancelling,
  ]);

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

      const targetMessage = messages.find((message) => message.id === messageId);

      if (!isPersistedChatMessageId(messageId)) {
        setError(null);
        setMessages((current) => current.filter((message) => message.id !== messageId));
        setPendingUserMessage(null);
        await sendMessage({ content: normalizedContent });
        return targetMessage
          ? {
              ...targetMessage,
              content: normalizedContent,
            }
          : null;
      }

      if (targetMessage && targetMessage.role !== "user") {
        setError("Somente perguntas do usuário podem ser reenviadas.");
        return null;
      }

      setError(null);

      // Limpa otimisticamente a resposta antiga: ao reenviar criamos uma nova
      // branch a partir desta pergunta, então tudo que vem depois dela sai da
      // visão e a pergunta editada já aparece persistida. Os logs de envio
      // passam a ser renderizados logo abaixo da pergunta (igual a um envio novo).
      setPendingUserMessage(null);
      setMessages((current) => {
        const targetIndex = current.findIndex((item) => item.id === messageId);

        if (targetIndex < 0) {
          return current;
        }

        const trimmed = current.slice(0, targetIndex + 1);
        const target = trimmed[targetIndex];

        trimmed[targetIndex] = {
          ...target,
          content: normalizedContent,
          metadata: {
            ...(target.metadata ?? {}),
            optimistic: false,
          },
        };

        return trimmed;
      });

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

      try {
        await resendMessage({
          sessionId: activeSession.id,
          messageId,
          content: normalizedContent,
          context: activeSession.context ?? "geral",
          responseMode: getResponseModeRef.current?.() ?? "normal",
          ...buildStreamCallbacks(activeSession, null, { refreshOnUserPersisted: true }),
        });

        return {
          id: messageId,
          session_id: activeSession.id,
          role: "user" as const,
          content: normalizedContent,
          metadata: targetMessage?.metadata ?? null,
          created_at: targetMessage?.created_at ?? new Date().toISOString(),
        };
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          finishSending(activeSession.id);
          return null;
        }

        const errorText = err instanceof Error ? err.message.toLowerCase() : "";
        const messageMissing =
          errorText.includes("não encontrada") ||
          errorText.includes("nao encontrada") ||
          errorText.includes("not found") ||
          errorText.includes("message_not_found");

        if (messageMissing) {
          finishSending(activeSession.id);
          resetStreamingUi();
          await sendMessage({ content: normalizedContent });
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
      resetStreamingUi,
      sendMessage,
    ],
  );

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

    if (userDismissedBackgroundStreamRef.current.has(activeSession.id)) {
      void loadMessages(activeSession.id, { userDismissedBackground: true });
      return;
    }

    if (
      (isSessionPending(activeSession.id) ||
        isSessionStreaming(activeSession.id) ||
        pendingUserMessage ||
        cancellingSessionIds.has(activeSession.id)) &&
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
    cancellingSessionIds,
    pendingUserMessage,
  ]);

  useEffect(() => {
    const sessionId = activeSession?.id;

    if (!sessionId || isSessionStreaming(sessionId) || playbackPayload) {
      return;
    }

    if (isSessionStreamDismissed(sessionId)) {
      unmarkSessionPending(sessionId);
      return;
    }

    const awaitingBackground =
      (isSessionPending(sessionId) && !pendingUserMessage) ||
      sessionAwaitingAssistantResponse(messages);

    if (!awaitingBackground) {
      return;
    }

    ensureAwaitingStreamUi(sessionId);

    const interval = window.setInterval(() => {
      if (isSessionStreamDismissed(sessionId)) {
        return;
      }

      void loadMessages(sessionId);
    }, 2500);

    return () => {
      window.clearInterval(interval);
    };
  }, [
    activeSession?.id,
    dismissedStreamRevision,
    isSessionPending,
    isSessionStreamDismissed,
    isSessionStreaming,
    loadMessages,
    messages,
    pendingUserMessage,
    playbackPayload,
    ensureAwaitingStreamUi,
    unmarkSessionPending,
  ]);

  const visibleMessages = useMemo(() => {
    let list = messages;

    const hideGeneratingPlaceholder =
      Boolean(activeSession) &&
      (isSessionStreaming(activeSession.id) ||
        isSessionPending(activeSession.id) ||
        cancellingSessionIds.has(activeSession.id) ||
        playbackPayload) &&
      list.length > 0 &&
      isAssistantGenerating(list[list.length - 1]);

    if (hideGeneratingPlaceholder) {
      list = list.slice(0, -1);
    }

    if (!pendingUserMessage) {
      return list;
    }

    if (!shouldAppendPendingUserMessage(list, pendingUserMessage)) {
      return list;
    }

    return [...list, pendingUserMessage];
  }, [activeSession, cancellingSessionIds, isSessionPending, isSessionStreaming, messages, pendingUserMessage, playbackPayload]);

  const isComposerBusy = isActiveSessionBusy();
  const isBackgroundAwaitingResponse =
    Boolean(activeSession) &&
    !isSessionStreamDismissed(activeSession.id) &&
    sessionAwaitingAssistantResponse(messages);
  const isStreamingActiveSession =
    Boolean(activeSession) &&
    !cancellingSessionIds.has(activeSession.id) &&
    (isSessionStreaming(activeSession.id) ||
      isSessionPending(activeSession.id) ||
      isPlaybackActive ||
      isBackgroundAwaitingResponse);

  const switchMessageBranch = useCallback(
    async (anchorUserMessageId: string, sourceUserMessageId?: string) => {
      const sessionId = activeSession?.id;

      if (!sessionId || isActiveSessionBusy() || branchSwitchingMessageId) {
        return;
      }

      setError(null);
      setBranchSwitchingMessageId(sourceUserMessageId ?? anchorUserMessageId);

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
      } finally {
        setBranchSwitchingMessageId(null);
      }
    },
    [
      activeSession?.id,
      branchSwitchingMessageId,
      isActiveSessionBusy,
      options.getAccessToken,
    ],
  );

  const continueFromMessage = useCallback(
    async (messageId: string) => {
      if (!activeSession || isActiveSessionBusy()) {
        return;
      }

      if (messageId.startsWith("optimistic-")) {
        setError("Aguarde a mensagem ser salva antes de continuar a partir daqui.");
        return;
      }

      const sourceMessage = messages.find((item) => item.id === messageId);

      if (!sourceMessage) {
        setError("Não encontrei a mensagem para continuar a partir daqui.");
        return;
      }

      const resendUserMessage = sourceMessage.role === "user";
      const questionText = resendUserMessage
        ? String(sourceMessage.content || "").trim()
        : "";

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
            forkResendUserMessage: resendUserMessage,
          },
          { getAccessToken: options.getAccessToken },
        );

        setSessions((current) => [newSession, ...current]);
        resetStreamingUi();
        activeSessionIdRef.current = newSession.id;
        setActiveSession(newSession);
        setMessages([]);
        setPendingUserMessage(null);

        await loadMessages(newSession.id);

        options.onSessionActivated?.(newSession.id, {
          agentId: newSession.agent_id ?? options.agentId ?? null,
          projectId: newSession.project_id ?? options.projectId ?? null,
        });

        if (resendUserMessage && questionText) {
          await sendMessage({ session: newSession, content: questionText });
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao continuar conversa.");
      }
    },
    [
      activeSession,
      isActiveSessionBusy,
      loadMessages,
      messages,
      options,
      resetStreamingUi,
      sendMessage,
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
    branchSwitchingMessageId,
    continueFromMessage,
  };
}
