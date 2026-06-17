import { type DragEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChatCanvas, type ChatCanvasDocument } from "../components/ChatCanvas";
import { ChatAgentHome } from "../components/ChatAgentHome";
import { ChatEmptyState } from "../components/ChatEmptyState";
import {
  ChatOnboardingTour,
  isOnboardingTourCompleted,
} from "../components/ChatOnboardingTour";
import "./ChatPage.css";
import "../layout/chat-layout.css";
import { useChatLayout } from "../../state/hooks/useChatLayout";
import { ChatInput, type ChatInputAttachment } from "../components/composer";
import { ChatInlineError } from "../components/ChatInlineError";
import { ChatAddContextDialog } from "../components/ChatAddContextDialog";
import { ChatContextBar, type ChatContextChip } from "../components/ChatContextBar";
import {
  ChatMemoryUsedDialog,
  type MemoryUsageView,
} from "../components/ChatMemoryUsedDialog";
import { ChatMessageList } from "../components/message";
import { ChatContextTopbar } from "../components/ChatContextTopbar";
import { ChatHelpPanel } from "../components/ChatHelpPanel";
import { ChatAnimatedPanel } from "../components/ChatAnimatedPanel";
import { ChatProjectHome } from "../components/ChatProjectHome";
import { ChatSidebar, type ChatSidebarView } from "../components/ChatSidebar";
import { useConfirmDialog } from "../components/useConfirmDialog";
import { usePromptDialog } from "../components/usePromptDialog";
import { useAlertDialog } from "../components/useAlertDialog";
import { setChatAlertHandler } from "../utils/chatNativeDialogs";
import {
  useChatShortcutPrompt,
  type ShortcutPromptOptions,
} from "../hooks/useChatShortcutPrompt";
import {
  resolveChatTopbarPresentation,
  resolvePreferredOperationalAgent,
} from "../../state/chatAgentActivation";
import {
  buildComposerTurnPayload,
  formatComposerPlaceholderParts,
  MAX_COMPOSER_AGENTS,
  MAX_COMPOSER_PROJECTS,
  removeContextId,
  resolveComposerContextBarFromLists,
  resolveEffectiveAgentIds,
  resolveEffectiveProjectIds,
  resolvePrimaryContextId,
  toggleContextId,
} from "../../state/chatComposerContext";
import {
  listComposerMentionCandidates,
  mergeMentionedContextIds,
  resolveMentionedContextIds,
} from "../../state/chatComposerMention";
import { isOperationalHomeStarter } from "../chatHomeStarters";
import {
  buildActiveContextSummary,
  collectActiveContextChips,
  contextChipKey,
  extractActivePreferenceHint,
  extractMemoryUsageFromMessages,
  inferContextChipOperationalRole,
  isPinnableContextKind,
  isUserContextItemKind,
  mergeContextChips,
  normalizeContextChips,
  resolvePresentationFormatForSend,
} from "../chatActiveContext";
import {
  buildContextPayloadFromMessage,
  buildContextTurnPayload,
  contextPayloadDedupKey,
  findPreviousUserMessage,
  listRecentConversationPicks,
  type ContextItemPayload,
} from "../chatContextFromMessage";
import {
  CHAT_SHORTCUT_PROMPT_COPY,
  extractProductCodeFromContextChips,
  hasUnresolvedShortcutPlaceholders,
  normalizeShortcutTemplate,
  resolveStarterPromptOptions,
  starterRequiresShortcutModal,
  type StarterInvokeContext,
} from "../chatShortcutPrompt";
import {
  readHomeCatalogCache,
  readStoredOnboardingProfileId,
  writeHomeCatalogCache,
} from "../chatOnboardingCache";
import { ChatAgentsPage } from "./ChatAgentsPage";
import { ChatProjectsPage } from "./ChatProjectsPage";
import {
  addChatSessionContextItem,
  addChatSessionMemoryPin,
  removeChatSessionContextItem,
  type SessionMemoryContextResponse,
  clearChatSessionMemory,
  createChatArtifact,
  createProjectTextSource,
  deleteChatSource,
  downloadChatAttachment,
  downloadChatSource,
  getAssistantCatalog,
  getChatCapabilities,
  getChatSessionMemoryContext,
  recordAssistantHelpEvent,
  listProjectSources,
  removeChatSessionMemoryPin,
  updateChatArtifact,
  uploadChatAttachment,
  uploadProjectSource,
} from "../../data/api/chatApi";
import {
  isAttachmentIndexPending,
  waitForSessionAttachmentIndexed,
} from "../../data/workspaceFileIngestPolling";
import { mapApiAttachmentToComposerStatus } from "../chatAttachmentStatus";
import {
  buildTypingCorrectionMetadata,
} from "../../state/chatTypingCorrection";
import { useChatTypingCorrection } from "../../state/hooks/useChatTypingCorrection";
import { getTypingCorrectionContent } from "../../content/messageComposerContent";
import type { ChatTypingCorrectionMetadata } from "../../data/api/chatTypes";
import { recordTypingCorrectionTelemetry } from "../typingCorrectionTelemetry";
import {
  buildChatAdminAgentHref,
  buildChatAgentActionsHref,
  buildChatAgentConfigHref,
  buildChatAgentHref,
  buildChatAgentSessionHref,
  buildChatAgentSkillsHref,
  buildChatHref,
  buildChatProjectConfigHref,
  buildChatProjectHref,
  buildChatProjectSessionHref,
  buildChatSessionHref,
  buildChatSessionHrefForSession,
  findAgentByRouteId,
  findProjectByRouteId,
  normalizeAgentRouteId,
  normalizeProjectRouteId,
  parseChatRoute,
  type ChatRoute,
} from "../../navigation/chatRoutes";
import {
  navigateChatHref,
  navigateChatSurface,
} from "../../navigation/chatNavigation";
import {
  getChatSidebarViewForRoute,
  getInitialActiveAgentPageId,
  getInitialAgentEditRequest,
  getInitialSelectedProjectId,
} from "../../navigation/chatRouteInitialState";
import { useChatRouteSync } from "../../state/hooks/useChatRouteSync";
import type {
  AssistantCatalogResponse,
  AssistantOnboardingPayload,
  AssistantContextualHighlight,
  ChatCanvasOpenPayload,
  ChatMessage,
  ChatPresentationFormatId,
} from "../../data/api/chatTypes";
import { useChatPresentationFormat } from "../../state/hooks/useChatPresentationFormat";
import { useChatResponseMode } from "../../state/hooks/useChatResponseMode";
import { useChatSession } from "../../state/hooks/useChatSession";
import { useChatWorkspace } from "../../state/hooks/useChatWorkspace";
import { getDisplayNameFromAccessToken } from "../../utils/authDisplayName";

const SIDEBAR_COLLAPSED_STORAGE_KEY = "minha-delpi-chat.sidebar-collapsed";


type ChatPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  pathname?: string;
  initialRoute?: ChatRoute;
  onOpenAdmin?: (agentId?: string) => void;
};


export function ChatPage({
  getAccessToken,
  pathname,
  initialRoute,
  onOpenAdmin,
}: ChatPageProps) {
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
  const { prompt, dialog: promptDialog } = usePromptDialog();
  const { alert: showAlert, dialog: alertDialog } = useAlertDialog();

  useEffect(() => {
    setChatAlertHandler((message, title) => {
      void showAlert({ message, title });
    });

    return () => {
      setChatAlertHandler((message, title) => {
        const prefix = title ? `${title}\n\n` : "";
        window.alert(`${prefix}${message}`);
      });
    };
  }, [showAlert]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(() =>
    getInitialSelectedProjectId(initialRoute),
  );
  const [activeAgentPageId, setActiveAgentPageId] = useState<string | null>(() =>
    getInitialActiveAgentPageId(initialRoute),
  );
  const [agentEditRequest, setAgentEditRequest] = useState<{
    id: string;
    requestKey: number;
  } | null>(() => getInitialAgentEditRequest(initialRoute));
  const [canManageAgents, setCanManageAgents] = useState(false);
  const [canManageOfficialAgents, setCanManageOfficialAgents] = useState(false);
  const [hasLoadedManageAgentsPermission, setHasLoadedManageAgentsPermission] = useState(false);
  const [canOpenAdmin, setCanOpenAdmin] = useState(false);
  const [typingCorrectionEnabled, setTypingCorrectionEnabled] = useState(true);

  const [contextAgentIds, setContextAgentIds] = useState<string[]>([]);
  const [contextProjectIds, setContextProjectIds] = useState<string[]>([]);
  const [removedComposerAgentIds, setRemovedComposerAgentIds] = useState<string[]>([]);
  const [removedComposerProjectIds, setRemovedComposerProjectIds] = useState<string[]>([]);

  function clearComposerOverlayContext() {
    setContextAgentIds([]);
    setContextProjectIds([]);
    setRemovedComposerAgentIds([]);
    setRemovedComposerProjectIds([]);
  }

  const [currentView, setCurrentView] = useState<ChatSidebarView>(() =>
    initialRoute ? getChatSidebarViewForRoute(initialRoute) : "chat",
  );
  const chatRoute = useMemo(() => parseChatRoute(pathname), [pathname]);
  const [userDisplayName, setUserDisplayName] = useState<string | null>(null);
  const [composerAttachments, setComposerAttachments] = useState<ChatInputAttachment[]>([]);
  const [projectSources, setProjectSources] = useState<Record<string, import("../../data/api/chatTypes").ChatWorkspaceSource[]>>({});
  const [isLoadingProjectSources, setIsLoadingProjectSources] = useState(false);
  const [isDraggingFile, setIsDraggingFile] = useState(false);
  const overlayAgentIds = resolveEffectiveAgentIds({
    pageAgentId: activeAgentPageId,
    contextAgentIds,
    excludedAgentIds: removedComposerAgentIds,
  });
  const overlayProjectIds = resolveEffectiveProjectIds({
    pageProjectId: selectedProjectId,
    contextProjectIds,
    excludedProjectIds: removedComposerProjectIds,
  });
  const requestedAgentId = resolvePrimaryContextId(overlayAgentIds);
  const requestedProjectId = resolvePrimaryContextId(overlayProjectIds);
  const [canvasDocument, setCanvasDocument] = useState<ChatCanvasDocument | null>(null);
  const [helpPanelOpen, setHelpPanelOpen] = useState(false);
  const [helpSearchQuery, setHelpSearchQuery] = useState("");
  const [helpCatalog, setHelpCatalog] = useState<AssistantCatalogResponse | null>(null);
  const [helpCatalogLoading, setHelpCatalogLoading] = useState(false);
  const [helpCatalogError, setHelpCatalogError] = useState<string | null>(null);
  const initialOnboardingProfileId = readStoredOnboardingProfileId();
  const initialHomeCatalogCache = readHomeCatalogCache(initialOnboardingProfileId);
  const [homeHighlights, setHomeHighlights] = useState<AssistantContextualHighlight[]>(
    () => initialHomeCatalogCache?.highlights ?? [],
  );
  const [homeOnboarding, setHomeOnboarding] = useState<AssistantOnboardingPayload | null>(
    () => initialHomeCatalogCache?.onboarding ?? null,
  );
  const [tourPlusMenuOpen, setTourPlusMenuOpen] = useState<boolean | null>(null);
  const [onboardingTourOpen, setOnboardingTourOpen] = useState(false);
  const [onboardingProfileId, setOnboardingProfileId] = useState<string | null>(
    initialOnboardingProfileId,
  );

  const openCanvasPanel = useCallback((payload: ChatCanvasOpenPayload) => {
    if (!payload.markdown.trim()) {
      return;
    }

    setCanvasDocument({
      title: payload.title || "Conteúdo do chat",
      markdown: payload.markdown,
      messageId: payload.sourceMessageId ?? payload.messageId ?? null,
      version: payload.version ?? null,
      documentType: payload.documentType ?? null,
    });
  }, []);

  type PromptAndSendParams = {
    content?: string;
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
    typingCorrection?: ChatTypingCorrectionMetadata;
  };

  const promptAndSendMessageRef = useRef<
    (params?: PromptAndSendParams, promptOptions?: ShortcutPromptOptions) => Promise<void>
  >(async () => undefined);
  const isShortcutPromptOpenRef = useRef<() => boolean>(() => false);
  const shortcutPromptResolvingRef = useRef(false);
  const resolveShortcutQueryRef = useRef<
    (raw: string, options?: ShortcutPromptOptions) => Promise<string | null>
  >(async () => null);
  const shortcutSendPromptOptionsRef = useRef<ShortcutPromptOptions>({
    ...CHAT_SHORTCUT_PROMPT_COPY.send,
    title: "Consulta ao chat",
  });
  const catalogProfileSyncedRef = useRef(false);
  const sendMessageWithOperationalAgentRef = useRef<
    (
      params: Parameters<typeof sendMessage>[0] & { content?: string },
      starterContext?: StarterInvokeContext,
    ) => Promise<void>
  >(async () => undefined);

  const {
    enabled: responseModesEnabled,
    modes: responseModes,
    responseMode,
    setResponseMode,
  } = useChatResponseMode({ getAccessToken });

  const getResponseMode = useCallback(() => responseMode, [responseMode]);
  const presentationFormatForSendRef = useRef<ChatPresentationFormatId>("auto");
  const getPresentationFormat = useCallback(
    () => presentationFormatForSendRef.current,
    [],
  );

  const {
    sessions,
    archivedSessions,
    activeSession,
    messages,
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
    isStreamingActiveSession,
    isPlaybackActive,
    isSessionProcessing,
    error,
    clearError,
    unansweredTurnRecovery,
    dismissUnansweredTurnRecovery,
    setDraft,
    sendMessage,
    cancelStreaming,
    loadArchivedSessions,
    startSession,
    selectSession,
    deleteSession,
    renameSession,
    pinSession,
    unpinSession,
    archiveSession,
    unarchiveSession,
    editAndResendMessage,
    setMessageFeedback,
    switchMessageBranch,
    branchSwitchingMessageId,
    continueFromMessage,
  } = useChatSession({
    getAccessToken,
    projectId: requestedProjectId,
    agentId: requestedAgentId,
    projectIds: overlayProjectIds,
    agentIds: overlayAgentIds,
    getResponseMode,
    getPresentationFormat,
    onSessionActivated: (sessionId) => {
      navigateChatHref(buildChatSessionHref(sessionId), { replace: true });
    },
    onOpenCanvas: openCanvasPanel,
    isShortcutPromptOpen: () => isShortcutPromptOpenRef.current(),
    onShortcutPromptRequired: (template) => {
      if (isShortcutPromptOpenRef.current()) {
        return;
      }

      void resolveShortcutQueryRef.current(
        template,
        shortcutSendPromptOptionsRef.current,
      );
    },
  });

  const effectiveAgentIds = resolveEffectiveAgentIds({
    pageAgentId: activeAgentPageId,
    sessionAgentId: activeSession?.agent_id,
    contextAgentIds,
    excludedAgentIds: removedComposerAgentIds,
  });
  const effectiveProjectIds = resolveEffectiveProjectIds({
    pageProjectId: selectedProjectId,
    sessionProjectId: activeSession?.project_id,
    contextProjectIds,
    excludedProjectIds: removedComposerProjectIds,
  });
  const {
    options: presentationFormatOptions,
    presentationFormat,
    setPresentationFormat,
    syncFromSessionChips,
  } = useChatPresentationFormat({
    sessionId: activeSession?.id ?? null,
    getAccessToken,
  });

  const typingCorrectionLabels = useMemo(() => getTypingCorrectionContent(), []);
  const {
    suggestion: typingSuggestion,
    dismissSuggestion: dismissTypingSuggestionState,
    clearSuggestion: clearTypingSuggestion,
  } = useChatTypingCorrection({
    draft,
    sessionId: activeSession?.id ?? null,
    enabled: typingCorrectionEnabled,
    getAccessToken,
  });

  const [contextMemoryCleared, setContextMemoryCleared] = useState(false);
  const [dismissedContextChipKeys, setDismissedContextChipKeys] = useState<string[]>([]);
  const [pinnedContextChips, setPinnedContextChips] = useState<ChatContextChip[]>([]);
  const [addContextDialogOpen, setAddContextDialogOpen] = useState(false);
  const [memoryUsedDialogOpen, setMemoryUsedDialogOpen] = useState(false);
  const [sessionMemoryUsage, setSessionMemoryUsage] = useState<MemoryUsageView | null>(
    null,
  );
  const contextAddInFlightRef = useRef<Set<string>>(new Set());

  const mergedContextChips = useMemo(() => {
    if (contextMemoryCleared) {
      return pinnedContextChips;
    }

    return mergeContextChips([
      pinnedContextChips,
      collectActiveContextChips(messages),
    ]);
  }, [messages, contextMemoryCleared, pinnedContextChips]);

  const activeContextChips = useMemo(() => {
    if (dismissedContextChipKeys.length === 0) {
      return mergedContextChips;
    }

    const hidden = new Set(dismissedContextChipKeys);

    return mergedContextChips.filter((chip) => !hidden.has(contextChipKey(chip)));
  }, [mergedContextChips, dismissedContextChipKeys]);

  const activeContextSummary = useMemo(
    () => buildActiveContextSummary(activeContextChips),
    [activeContextChips],
  );

  useEffect(() => {
    presentationFormatForSendRef.current = resolvePresentationFormatForSend(
      presentationFormat,
      activeContextChips,
    );
  }, [presentationFormat, activeContextChips]);

  const activePreferenceHint = useMemo(
    () => extractActivePreferenceHint(activeContextChips),
    [activeContextChips],
  );

  const memoryUsageFromMessages = useMemo(
    () => extractMemoryUsageFromMessages(messages),
    [messages],
  );

  const activeMemoryUsage = sessionMemoryUsage ?? memoryUsageFromMessages;

  const shortcutPrefillContext = useMemo(
    () => ({
      productCode: extractProductCodeFromContextChips(activeContextChips),
    }),
    [activeContextChips],
  );
  const { resolveShortcutQuery, shortcutPromptDialog, isShortcutPromptOpen } =
    useChatShortcutPrompt({
      getPrefillContext: () => shortcutPrefillContext,
    });

  const shortcutSendPromptOptions = useMemo<ShortcutPromptOptions>(
    () => ({
      ...CHAT_SHORTCUT_PROMPT_COPY.send,
      title: "Consulta ao chat",
    }),
    [],
  );

  const promptAndSendMessage = useCallback(
    async (
      params: PromptAndSendParams = {},
      promptOptions: ShortcutPromptOptions = shortcutSendPromptOptions,
    ) => {
      const raw = (params.content ?? draft).trim();

      if (!raw) {
        return;
      }

      clearError();
      shortcutPromptResolvingRef.current = true;

      let resolved: string | null = null;

      try {
        resolved = await resolveShortcutQuery(raw, promptOptions);
      } finally {
        shortcutPromptResolvingRef.current = false;
      }

      if (!resolved) {
        if (params.content == null) {
          setDraft(raw);
        }

        return;
      }

      if (params.content == null) {
        setDraft("");
      }

      if (hasUnresolvedShortcutPlaceholders(resolved)) {
        const recovered = await resolveShortcutQuery(raw, promptOptions);

        if (!recovered || hasUnresolvedShortcutPlaceholders(recovered)) {
          return;
        }

        const sendOperational = sendMessageWithOperationalAgentRef.current;

        if (sendOperational) {
          await sendOperational({ ...params, content: recovered });
        } else {
          await sendMessage({ ...params, content: recovered });
        }

        return;
      }

      const sendOperational = sendMessageWithOperationalAgentRef.current;

      if (sendOperational) {
        await sendOperational({ ...params, content: resolved });
      } else {
        await sendMessage({ ...params, content: resolved });
      }
    },
    [clearError, draft, resolveShortcutQuery, sendMessage, setDraft, shortcutSendPromptOptions],
  );

  useEffect(() => {
    promptAndSendMessageRef.current = promptAndSendMessage;
    isShortcutPromptOpenRef.current = isShortcutPromptOpen;
    resolveShortcutQueryRef.current = resolveShortcutQuery;
    shortcutSendPromptOptionsRef.current = shortcutSendPromptOptions;
  }, [isShortcutPromptOpen, promptAndSendMessage, resolveShortcutQuery, shortcutSendPromptOptions]);

  const applySessionMemoryContext = useCallback(
    (response: SessionMemoryContextResponse) => {
      setPinnedContextChips(normalizeContextChips(response.chips));
      setSessionMemoryUsage(response.usage ?? null);
      syncFromSessionChips(normalizeContextChips(response.chips));
    },
    [syncFromSessionChips],
  );

  useEffect(() => {
    setRemovedComposerAgentIds([]);
    setRemovedComposerProjectIds([]);
  }, [activeSession?.id]);

  useEffect(() => {
    setContextMemoryCleared(false);
    setDismissedContextChipKeys([]);
    setPinnedContextChips([]);
    setAddContextDialogOpen(false);
    setSessionMemoryUsage(null);
  }, [activeSession?.id]);

  useEffect(() => {
    const sessionId = activeSession?.id;

    if (!sessionId) {
      return;
    }

    let cancelled = false;

    void getChatSessionMemoryContext(sessionId, { getAccessToken })
      .then((response) => {
        if (cancelled) {
          return;
        }

        applySessionMemoryContext(response);
      })
      .catch(() => {
        /* memória opcional — chips de turno continuam disponíveis */
      });

    return () => {
      cancelled = true;
    };
  }, [activeSession?.id, applySessionMemoryContext, getAccessToken]);

  const handleDismissContextChip = useCallback((chip: ChatContextChip) => {
    const key = contextChipKey(chip);

    setDismissedContextChipKeys((current) =>
      current.includes(key) ? current : [...current, key],
    );

    if (!activeSession?.id) {
      return;
    }

    if (isUserContextItemKind(chip.kind)) {
      const itemId = chip.itemId?.trim() || chip.value;
      void removeChatSessionContextItem(activeSession.id, itemId, { getAccessToken })
        .then((response) => {
          applySessionMemoryContext(response);
        })
        .catch(() => {
          /* dismiss local já aplicado */
        });

      return;
    }

    if (!isPinnableContextKind(chip.kind)) {
      return;
    }

    void removeChatSessionMemoryPin(activeSession.id, chip.kind, { getAccessToken })
      .then((response) => {
        applySessionMemoryContext(response);
      })
      .catch(() => {
        /* dismiss local já aplicado */
      });
  }, [activeSession?.id, getAccessToken, applySessionMemoryContext]);

  const handlePinContextChip = useCallback(
    (chip: ChatContextChip) => {
      if (!isPinnableContextKind(chip.kind)) {
        return;
      }

      if (!activeSession?.id) {
        setPinnedContextChips((current) => mergeContextChips([current, [chip]]));
        setContextMemoryCleared(false);
        return;
      }

      const role =
        chip.kind === "context"
          ? inferContextChipOperationalRole(chip)
          : chip.kind;

      if (chip.kind === "context" && !role) {
        return;
      }

      void addChatSessionMemoryPin(
        activeSession.id,
        {
          kind: role === "product" || role === "branch" || role === "warehouse" ? role : chip.kind,
          value: chip.label || chip.value,
        },
        { getAccessToken },
      )
        .then((response) => {
          applySessionMemoryContext(response);
          setContextMemoryCleared(false);
        })
        .catch(() => {
          setPinnedContextChips((current) => mergeContextChips([current, [chip]]));
        });
    },
    [activeSession?.id, applySessionMemoryContext, getAccessToken],
  );

  const handleViewMemoryUsed = useCallback(() => {
    if (activeSession?.id) {
      void getChatSessionMemoryContext(activeSession.id, { getAccessToken })
        .then((response) => {
          applySessionMemoryContext(response);
          setMemoryUsedDialogOpen(true);
        })
        .catch(() => {
          if (activeMemoryUsage) {
            setMemoryUsedDialogOpen(true);
          }
        });

      return;
    }

    if (activeMemoryUsage) {
      setMemoryUsedDialogOpen(true);
    }
  }, [activeMemoryUsage, activeSession?.id, applySessionMemoryContext, getAccessToken]);

  const handleAddContextPayload = useCallback(
    (payload: ContextItemPayload) => {
      setAddContextDialogOpen(false);

      if (!activeSession?.id) {
        return;
      }

      const dedupKey = contextPayloadDedupKey(payload);

      if (dedupKey) {
        if (contextAddInFlightRef.current.has(dedupKey)) {
          return;
        }

        const alreadyPinned = pinnedContextChips.some(
          (chip) => contextChipKey(chip) === dedupKey,
        );

        if (alreadyPinned) {
          return;
        }

        contextAddInFlightRef.current.add(dedupKey);
      }

      void addChatSessionContextItem(activeSession.id, payload, { getAccessToken })
        .then((response) => {
          applySessionMemoryContext(response);
          setContextMemoryCleared(false);
          setDismissedContextChipKeys([]);
        })
        .catch(() => {
          /* erro silencioso — usuário pode tentar de novo */
        })
        .finally(() => {
          if (dedupKey) {
            contextAddInFlightRef.current.delete(dedupKey);
          }
        });
    },
    [
      activeSession?.id,
      applySessionMemoryContext,
      getAccessToken,
      pinnedContextChips,
    ],
  );

  const handleAddMessageToContext = useCallback(
    (message: ChatMessage) => {
      const payload = buildContextPayloadFromMessage(message);

      if (payload) {
        handleAddContextPayload(payload);
      }
    },
    [handleAddContextPayload],
  );

  const handleAddMessageTurnToContext = useCallback(
    (answerMessage: ChatMessage) => {
      const questionMessage = findPreviousUserMessage(messages, answerMessage.id);
      const payload =
        questionMessage && buildContextTurnPayload(questionMessage, answerMessage);

      if (payload) {
        handleAddContextPayload(payload);
      }
    },
    [handleAddContextPayload, messages],
  );

  const recentConversationPicks = useMemo(
    () => listRecentConversationPicks(messages),
    [messages],
  );

  const handleClearActiveContext = useCallback(() => {
    void (async () => {
      if (activeSession?.id) {
        try {
          await clearChatSessionMemory(activeSession.id, { getAccessToken });
        } catch {
          // fallback: mensagem explícita ainda aciona limpeza no pipeline
          await sendMessage({
            content:
              "a partir de agora, desconsidere produto, filial e preferências anteriores desta conversa.",
          });
          return;
        }
      }

      setContextMemoryCleared(true);
      setDismissedContextChipKeys([]);
      setPinnedContextChips([]);
      setSessionMemoryUsage(null);
    })();
  }, [activeSession?.id, getAccessToken, sendMessage]);

  const {
    agents,
    projects,
    isLoadingAgents,
    isLoadingProjects,
    workspaceError,
    clearWorkspaceError,
    addAgent,
    editAgent,
    syncAgent,
    removeAgent,
    addProject,
    editProject,
    removeProject,
    loadAgents,
  } = useChatWorkspace({ getAccessToken });

  const selectedProject = projects.find((project) => project.id === selectedProjectId);
  const projectSettingsOpen =
    chatRoute.kind === "project-config" &&
    selectedProject?.id === chatRoute.projectId;
  const agentSubRoute = useMemo(() => {
    if (chatRoute.kind === "agent-skills") {
      return { kind: "skills" as const, agentId: chatRoute.agentId };
    }

    if (chatRoute.kind === "agent-actions") {
      return {
        kind: "actions" as const,
        agentId: chatRoute.agentId,
        providerKey: chatRoute.providerKey ?? null,
      };
    }

    return null;
  }, [chatRoute]);
  const activeAgentPage = agents.find((agent) => agent.id === activeAgentPageId);
  const conversationAgentId = activeSession?.agent_id ?? activeAgentPageId;
  const effectiveComposerProjects = effectiveProjectIds
    .map((id) => projects.find((project) => project.id === id))
    .filter((project): project is NonNullable<typeof project> => Boolean(project));
  const effectiveComposerAgents = effectiveAgentIds
    .map((id) => agents.find((agent) => agent.id === id))
    .filter((agent): agent is NonNullable<typeof agent> => Boolean(agent));
  const composerContextBarItems = resolveComposerContextBarFromLists({
    pageAgentId: activeAgentPageId,
    pageProjectId: selectedProject?.id ?? null,
    sessionAgentId: activeSession?.agent_id,
    sessionProjectId: activeSession?.project_id,
    contextAgentIds,
    contextProjectIds,
    excludedAgentIds: removedComposerAgentIds,
    excludedProjectIds: removedComposerProjectIds,
  });
  const hasActiveConversation =
    messages.length > 0 ||
    isStreamingActiveSession ||
    (isStreamingActiveSession && Boolean(streamingAnswer));
  const isConversationEmpty = !hasActiveConversation;
  const chatTopbarPresentation = resolveChatTopbarPresentation({
    routeAgentPageId: activeAgentPageId,
    routeAgentName: activeAgentPage?.name ?? null,
    routeProjectId: selectedProjectId,
    routeProjectName: selectedProject?.name ?? null,
  });
  const helpAgentId =
    contextAgentIds[0] ?? conversationAgentId ?? activeAgentPageId ?? undefined;
  const mentionCandidates = useMemo(
    () =>
      listComposerMentionCandidates({
        agents: agents.map((agent) => ({ id: agent.id, name: agent.name })),
        projects: projects.map((project) => ({ id: project.id, name: project.name })),
      }),
    [agents, projects],
  );

  const sendMessageWithOperationalAgent = useCallback(
    async (
      params: Parameters<typeof sendMessage>[0] & { content?: string },
      starterContext: StarterInvokeContext = {},
    ) => {
      let agentId = requestedAgentId;

      if (
        !agentId &&
        isOperationalHomeStarter({
          starterId: starterContext.starterId,
          query: params.content ?? draft,
          featureId: starterContext.featureId,
        })
      ) {
        const preferred = resolvePreferredOperationalAgent(agents);

        if (preferred) {
          agentId = preferred;
          setContextAgentIds((current) =>
            toggleContextId(current, preferred, MAX_COMPOSER_AGENTS),
          );
        }
      }

      const messageContent = params.content ?? draft;
      const mentioned = resolveMentionedContextIds(messageContent, mentionCandidates);
      const resolvedAgentIds = agentId
        ? [agentId, ...effectiveAgentIds.filter((id) => id !== agentId)].slice(
            0,
            MAX_COMPOSER_AGENTS,
          )
        : effectiveAgentIds;
      const mergedContext = mergeMentionedContextIds({
        overlayAgentIds: resolvedAgentIds,
        mentionAgentIds: mentioned.agentIds,
        overlayProjectIds: effectiveProjectIds,
        mentionProjectIds: mentioned.projectIds,
      });
      const turnPayload = buildComposerTurnPayload({
        effectiveAgentIds: mergedContext.agentIds,
        effectiveProjectIds: mergedContext.projectIds,
      });

      await sendMessage({
        ...params,
        ...turnPayload,
        turnContext: {
          agents: mergedContext.agentIds
            .map((id) => agents.find((entry) => entry.id === id))
            .filter((entry): entry is NonNullable<typeof entry> => Boolean(entry))
            .map((entry) => ({ id: entry.id, name: entry.name })),
          projects: mergedContext.projectIds
            .map((id) => projects.find((entry) => entry.id === id))
            .filter((entry): entry is NonNullable<typeof entry> => Boolean(entry))
            .map((entry) => ({ id: entry.id, name: entry.name })),
        },
      });
    },
    [
      agents,
      draft,
      effectiveAgentIds,
      effectiveProjectIds,
      mentionCandidates,
      projects,
      sendMessage,
    ],
  );

  useEffect(() => {
    sendMessageWithOperationalAgentRef.current = sendMessageWithOperationalAgent;
  }, [sendMessageWithOperationalAgent]);

  const handleDismissTypingSuggestion = useCallback(() => {
    dismissTypingSuggestionState();
  }, [dismissTypingSuggestionState]);

  const handleAcceptTypingSuggestion = useCallback(async () => {
    if (!typingSuggestion) {
      return;
    }

    const metadata = buildTypingCorrectionMetadata(typingSuggestion, true);
    recordTypingCorrectionTelemetry("typing_correction_accepted", {
      original: typingSuggestion.original,
      corrected: typingSuggestion.corrected,
      changeCount: typingSuggestion.changes.length,
    });
    clearTypingSuggestion();
    setDraft("");

    await sendMessageWithOperationalAgent({
      content: typingSuggestion.corrected,
      typingCorrection: metadata,
    });
  }, [
    clearTypingSuggestion,
    sendMessageWithOperationalAgent,
    setDraft,
    typingSuggestion,
  ]);

  useEffect(() => {
    if (!helpPanelOpen) {
      return;
    }

    const timer = window.setTimeout(() => {
      setHelpCatalogLoading(true);
      setHelpCatalogError(null);

      void getAssistantCatalog({
        getAccessToken,
        query: helpSearchQuery,
        agentId: helpAgentId,
      })
        .then((payload) => {
          setHelpCatalog(payload);
        })
        .catch((error: unknown) => {
          const message =
            error instanceof Error
              ? error.message
              : "Não foi possível carregar a ajuda do chat.";

          setHelpCatalogError(message);
          setHelpCatalog(null);
        })
        .finally(() => {
          setHelpCatalogLoading(false);
        });
    }, 280);

    return () => {
      window.clearTimeout(timer);
    };
  }, [getAccessToken, helpAgentId, helpPanelOpen, helpSearchQuery]);

  useEffect(() => {
    if (!helpPanelOpen) {
      return;
    }

    void recordAssistantHelpEvent({ event: "help_panel_open" }, { getAccessToken });
  }, [getAccessToken, helpPanelOpen]);

  const selectedProjectSessions = selectedProjectId
    ? sessions.filter((session) => session.project_id === selectedProjectId)
    : [];

  const { isDesktop, isLandscape, isNarrow } = useChatLayout();
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    return localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY) === "true";
  });

  function closeMobileSidebar() {
    setIsMobileSidebarOpen(false);
  }

  const applyChatRoute = useCallback(
    (route: ChatRoute) => {
      const resolveRouteAgent = (routeId: string) =>
        findAgentByRouteId(agents, routeId);

      const resolveRouteProject = (routeId: string) =>
        findProjectByRouteId(projects, routeId);

      const hasOutboundInFlight =
        messages.some((message) => message.metadata?.optimistic === true) ||
        Boolean(streamingStatus) ||
        isStreamingActiveSession;

      const shouldPreserveAgentCompose =
        (route.kind === "agent" || route.kind === "agent-session") &&
        hasOutboundInFlight &&
        activeAgentPageId === resolveRouteAgent(route.agentId)?.id;

      const shouldPreserveProjectCompose =
        (route.kind === "project" || route.kind === "project-session") &&
        hasOutboundInFlight &&
        selectedProjectId === route.projectId &&
        (!activeSession || activeSession.project_id === route.projectId);

      switch (route.kind) {
        case "home": {
          if (
            !activeSession &&
            !selectedProjectId &&
            !activeAgentPageId &&
            currentView === "chat"
          ) {
            return;
          }

          if (hasOutboundInFlight) {
            return;
          }

          clearWorkspaceError();
          clearError();
          setCanvasDocument(null);
          setComposerAttachments([]);
          setSelectedProjectId(null);
          setActiveAgentPageId(null);
          clearComposerOverlayContext();
          setCurrentView("chat");
          void startSession();
          closeMobileSidebar();
          break;
        }
        case "session": {
          const session = sessions.find((item) => item.id === route.sessionId);

          if (!session) {
            return;
          }

          if (activeSession?.id === route.sessionId) {
            closeMobileSidebar();
            return;
          }

          clearWorkspaceError();
          clearError();
          setCanvasDocument(null);
          setComposerAttachments([]);
          setSelectedProjectId(session.project_id ?? null);
          setActiveAgentPageId(session.agent_id ?? null);
          clearComposerOverlayContext();
          setCurrentView("chat");
          selectSession(session);
          closeMobileSidebar();

          if (session.agent_id) {
            navigateChatHref(
              buildChatAgentSessionHref(session.agent_id, session.id),
              { replace: true },
            );
          } else if (session.project_id) {
            navigateChatHref(
              buildChatProjectSessionHref(session.project_id, session.id),
              { replace: true },
            );
          }

          break;
        }
        case "project-session": {
          const session = sessions.find((item) => item.id === route.sessionId);
          const routeProject = resolveRouteProject(route.projectId);

          if (!routeProject) {
            if (!normalizeProjectRouteId(route.projectId)) {
              navigateChatHref(buildChatHref({ kind: "projects" }), { replace: true });
            }
            return;
          }

          if (session) {
            if (activeSession?.id === route.sessionId) {
              if (selectedProjectId !== routeProject.id) {
                setSelectedProjectId(routeProject.id);
              }
              closeMobileSidebar();
              return;
            }

            clearWorkspaceError();
            clearError();
            setCanvasDocument(null);
            setComposerAttachments([]);
            setSelectedProjectId(routeProject.id);
            setActiveAgentPageId(null);
            clearComposerOverlayContext();
            setCurrentView("chat");
            selectSession(session);
            closeMobileSidebar();
            break;
          }

          if (shouldPreserveProjectCompose) {
            closeMobileSidebar();
            return;
          }

          if (selectedProjectId === routeProject.id && !activeSession) {
            closeMobileSidebar();
            return;
          }

          clearWorkspaceError();
          clearError();
          setCanvasDocument(null);
          setComposerAttachments([]);
          setSelectedProjectId(routeProject.id);
          setActiveAgentPageId(null);
          clearComposerOverlayContext();
          setCurrentView("chat");
          void startSession();
          closeMobileSidebar();
          break;
        }
        case "agent-session": {
          const session = sessions.find((item) => item.id === route.sessionId);
          const routeAgent = resolveRouteAgent(route.agentId);

          if (!routeAgent) {
            if (!normalizeAgentRouteId(route.agentId)) {
              navigateChatHref(buildChatHref({ kind: "agents" }), { replace: true });
            }
            return;
          }

          if (session) {
            if (activeSession?.id === route.sessionId) {
              if (activeAgentPageId !== routeAgent.id) {
                setActiveAgentPageId(routeAgent.id);
              }
              closeMobileSidebar();
              return;
            }

            clearWorkspaceError();
            clearError();
            setCanvasDocument(null);
            setComposerAttachments([]);
            setSelectedProjectId(session.project_id ?? null);
            setActiveAgentPageId(routeAgent.id);
            clearComposerOverlayContext();
            setCurrentView("chat");
            selectSession(session);
            closeMobileSidebar();
            break;
          }

          if (shouldPreserveAgentCompose) {
            closeMobileSidebar();
            return;
          }

          if (activeAgentPageId === routeAgent.id && !activeSession) {
            closeMobileSidebar();
            return;
          }

          clearWorkspaceError();
          clearError();
          setCanvasDocument(null);
          setComposerAttachments([]);
          setSelectedProjectId(null);
          setActiveAgentPageId(routeAgent.id);
          clearComposerOverlayContext();
          setCurrentView("chat");
          void startSession();
          closeMobileSidebar();
          break;
        }
        case "project":
        case "project-config": {
          const routeProject = resolveRouteProject(route.projectId);

          if (!routeProject) {
            if (!normalizeProjectRouteId(route.projectId)) {
              navigateChatHref(buildChatHref({ kind: "projects" }), { replace: true });
            }
            return;
          }

          if (shouldPreserveProjectCompose) {
            closeMobileSidebar();
            return;
          }

          if (selectedProjectId === routeProject.id && !activeSession) {
            closeMobileSidebar();
            return;
          }

          clearWorkspaceError();
          clearError();
          setCanvasDocument(null);
          setComposerAttachments([]);
          setSelectedProjectId(routeProject.id);
          setActiveAgentPageId(null);
          clearComposerOverlayContext();
          setCurrentView("chat");
          void startSession();
          closeMobileSidebar();
          break;
        }
        case "agent": {
          const routeAgent = resolveRouteAgent(route.agentId);

          if (!routeAgent) {
            if (!normalizeAgentRouteId(route.agentId)) {
              navigateChatHref(buildChatHref({ kind: "agents" }), { replace: true });
            }
            return;
          }

          if (shouldPreserveAgentCompose) {
            closeMobileSidebar();
            return;
          }

          if (activeAgentPageId === routeAgent.id && !activeSession) {
            closeMobileSidebar();
            return;
          }

          clearWorkspaceError();
          clearError();
          setCanvasDocument(null);
          setComposerAttachments([]);
          setSelectedProjectId(null);
          setActiveAgentPageId(routeAgent.id);
          clearComposerOverlayContext();
          setCurrentView("chat");
          void startSession();
          closeMobileSidebar();
          break;
        }
        case "agent-config": {
          const routeAgent = resolveRouteAgent(route.agentId);

          if (!routeAgent) {
            return;
          }

          if (
            currentView === "agents" &&
            agentEditRequest?.id === routeAgent.id &&
            !agentSubRoute
          ) {
            closeMobileSidebar();
            return;
          }

          setAgentEditRequest({
            id: routeAgent.id,
            requestKey: Date.now(),
          });
          setCurrentView("agents");
          closeMobileSidebar();
          break;
        }
        case "agent-skills":
        case "agent-actions": {
          const routeAgent = resolveRouteAgent(route.agentId);

          if (!routeAgent) {
            return;
          }

          if (
            currentView === "agents" &&
            agentSubRoute?.agentId === routeAgent.id &&
            (route.kind === "agent-skills"
              ? agentSubRoute.kind === "skills"
              : agentSubRoute.kind === "actions" &&
                (agentSubRoute.providerKey ?? null) === (route.providerKey ?? null))
          ) {
            closeMobileSidebar();
            return;
          }

          setAgentEditRequest(null);
          setCurrentView("agents");
          closeMobileSidebar();
          break;
        }
        case "agents": {
          if (currentView === "agents") {
            closeMobileSidebar();
            return;
          }

          setCurrentView("agents");
          closeMobileSidebar();
          break;
        }
        case "projects": {
          if (currentView === "projects") {
            closeMobileSidebar();
            return;
          }

          setCurrentView("projects");
          closeMobileSidebar();
          break;
        }
        default:
          break;
      }
    },
    [
      activeAgentPageId,
      agentEditRequest?.id,
      agentSubRoute,
      agents,
      projects,
      activeSession,
      activeSession?.id,
      clearError,
      clearWorkspaceError,
      currentView,
      isSessionProcessing,
      isStreamingActiveSession,
      messages,
      selectSession,
      selectedProjectId,
      sessions,
      startSession,
      streamingStatus,
    streamingActivityLog,
    ],
  );

  const navigateToChatSurface = useCallback(
    (href: string, options?: { replace?: boolean }) => {
      navigateChatSurface(href, {
        replace: options?.replace,
        onApplyRoute: applyChatRoute,
      });
    },
    [applyChatRoute],
  );

  useChatRouteSync({
    pathname,
    sessions,
    workspaceReady: !isLoadingAgents && !isLoadingProjects,
    workspaceRevision: agents.length + projects.length,
    onApplyRoute: applyChatRoute,
  });

  function openMobileSidebar() {
    setIsMobileSidebarOpen(true);
  }

  useEffect(() => {
    localStorage.setItem(
      SIDEBAR_COLLAPSED_STORAGE_KEY,
      String(isSidebarCollapsed),
    );
  }, [isSidebarCollapsed]);

  useEffect(() => {
    if (isDesktop) {
      setIsMobileSidebarOpen(false);
    }
  }, [isDesktop]);

  useEffect(() => {
    if (!isMobileSidebarOpen) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        closeMobileSidebar();
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMobileSidebarOpen]);

  useEffect(() => {
    if (
      hasLoadedManageAgentsPermission &&
      currentView === "agents" &&
      !canManageAgents
    ) {
      setAgentEditRequest(null);
      setCurrentView("chat");
    }
  }, [currentView, canManageAgents, hasLoadedManageAgentsPermission]);

  function openProjectConfig(projectId: string) {
    navigateChatHref(buildChatProjectConfigHref(projectId));
  }

  function closeProjectConfig(projectId: string) {
    navigateChatHref(buildChatProjectHref(projectId));
  }

  function openAgentSkills(agentId: string) {
    navigateChatHref(buildChatAgentSkillsHref(agentId));
  }

  function openAgentActions(agentId: string, providerKey?: string | null) {
    navigateChatHref(buildChatAgentActionsHref(agentId, providerKey));
  }

  function openAdminForAgent(agentId: string) {
    navigateChatHref(buildChatAdminAgentHref(agentId));
  }

  function openAgentConfig(agentId: string) {
    navigateChatHref(buildChatAgentConfigHref(agentId));
  }

  function closeAgentConfig() {
    navigateChatHref(buildChatHref({ kind: "agents" }));
  }

  function openAgentsDirectory() {
    clearWorkspaceError();
    setCurrentView("agents");
    navigateChatHref(buildChatHref({ kind: "agents" }));
  }

  function openProjectsDirectory() {
    clearWorkspaceError();
    setCurrentView("projects");
    navigateChatHref(buildChatHref({ kind: "projects" }));
  }


  useEffect(() => {
    let isMounted = true;

    async function loadUserDisplayName() {
      const token = await getAccessToken?.();
      const displayName = getDisplayNameFromAccessToken(token);

      if (isMounted) {
        setUserDisplayName(displayName);
      }
    }

    void loadUserDisplayName();

    return () => {
      isMounted = false;
    };
  }, [getAccessToken]);


  useEffect(() => {
    let isMounted = true;

    async function loadToolManagementPermission() {
      setHasLoadedManageAgentsPermission(false);

      try {
        const capabilities = await getChatCapabilities({ getAccessToken });

        if (isMounted) {
          setCanManageAgents(capabilities.canManageAgents);
          setCanManageOfficialAgents(capabilities.canManageOfficialAgents);
          setCanOpenAdmin(
            capabilities.canOpenAdmin === true || capabilities.isSuperadmin === true,
          );
          setTypingCorrectionEnabled(capabilities.typingCorrectionEnabled !== false);
        }
      } catch {
        if (isMounted) {
          setCanManageAgents(false);
          setCanManageOfficialAgents(false);
          setCanOpenAdmin(false);
          setTypingCorrectionEnabled(true);
        }
      } finally {
        if (isMounted) {
          setHasLoadedManageAgentsPermission(true);
        }
      }
    }

    void loadToolManagementPermission();

    return () => {
      isMounted = false;
    };
  }, [getAccessToken]);

  async function loadProjectSources(projectId: string) {
    setIsLoadingProjectSources(true);

    try {
      const sources = await listProjectSources(projectId, { getAccessToken });
      setProjectSources((current) => ({
        ...current,
        [projectId]: sources,
      }));
    } finally {
      setIsLoadingProjectSources(false);
    }
  }

  useEffect(() => {
    if (selectedProjectId) {
      void loadProjectSources(selectedProjectId);
    }
  }, [selectedProjectId]);

  async function saveCanvasDocument(document: ChatCanvasDocument) {
    if (!activeSession) {
      return;
    }

    setCanvasDocument({
      ...document,
      isSaving: true,
    });

    try {
      const artifact = document.id
        ? await updateChatArtifact(
            document.id,
            {
              title: document.title,
              content: document.markdown,
            },
            { getAccessToken },
          )
        : await createChatArtifact(
            activeSession.id,
            {
              type: "markdown",
              title: document.title,
              content: document.markdown,
              messageId: document.messageId ?? null,
              metadata: {
                origin: "canvas",
              },
            },
            { getAccessToken },
          );

      setCanvasDocument({
        id: artifact.id,
        messageId: artifact.message_id,
        title: artifact.title,
        markdown: artifact.content,
        isSaving: false,
        isSaved: true,
      });
    } catch {
      setCanvasDocument({
        ...document,
        isSaving: false,
        isSaved: false,
      });
    }
  }

  async function handleStartSession() {
    setCanvasDocument(null);
    setComposerAttachments([]);
    await startSession();
  }

  function handleStartGeneralSession() {
    navigateToChatSurface(buildChatHref({ kind: "home" }));
  }

  function handleSelectSession(session: typeof sessions[number]) {
    clearWorkspaceError();
    clearError();
    setCanvasDocument(null);
    setComposerAttachments([]);
    setSelectedProjectId(session.project_id ?? null);
    setActiveAgentPageId(session.agent_id ?? null);
    clearComposerOverlayContext();
    setCurrentView("chat");
    selectSession(session);
    navigateChatHref(buildChatSessionHrefForSession(session));
    closeMobileSidebar();
  }

  async function handleDeleteSession(sessionId: string) {
    setCanvasDocument(null);
    return deleteSession(sessionId);
  }

  const uploadComposerAttachment = useCallback(
    async (sessionId: string, localId: string, file: File) => {
      setComposerAttachments((current) =>
        current.map((item) =>
          item.id === localId ? { ...item, status: "uploading" } : item,
        ),
      );

      try {
        const uploaded = await uploadChatAttachment(sessionId, file, { getAccessToken });
        let resolvedAttachment = uploaded;

        if (isAttachmentIndexPending(uploaded.status)) {
          const settled = await waitForSessionAttachmentIndexed(sessionId, uploaded.id, {
            getAccessToken,
          });

          if (settled) {
            resolvedAttachment = settled;
          }
        }

        const metadata = resolvedAttachment.metadata as Record<string, unknown> | null;
        const readingStatus =
          typeof metadata?.readingStatus === "string" ? metadata.readingStatus : undefined;

        setComposerAttachments((current) =>
          current.map((item) =>
            item.id === localId
              ? {
                  ...item,
                  status: mapApiAttachmentToComposerStatus(resolvedAttachment.status),
                  serverAttachmentId: resolvedAttachment.id,
                  readingStatus,
                }
              : item,
          ),
        );
      } catch {
        setComposerAttachments((current) =>
          current.map((item) =>
            item.id === localId
              ? { ...item, status: "failed", readingStatus: "Falha no envio" }
              : item,
          ),
        );
      }
    },
    [getAccessToken],
  );

  function handleAttachFiles(files: File[]) {
    const validFiles = files.filter((file) => file.size > 0);

    if (validFiles.length < files.length) {
      void showAlert({
        title: "Anexo inválido",
        message: "Arquivos vazios não podem ser anexados.",
      });
    }

    const nextAttachments: ChatInputAttachment[] = validFiles.map((file) => ({
      id: `${file.name}-${file.size}-${file.lastModified}-${crypto.randomUUID()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      file,
      status: "queued",
    }));

    if (nextAttachments.length === 0) {
      return;
    }

    setComposerAttachments((current) => [...current, ...nextAttachments].slice(0, 10));

    if (activeSession?.id) {
      for (const attachment of nextAttachments) {
        void uploadComposerAttachment(activeSession.id, attachment.id, attachment.file);
      }
    }
  }

  function hasDraggedFiles(event: DragEvent<HTMLElement>) {
    return Array.from(event.dataTransfer.types).includes("Files");
  }

  function handleChatDragEnter(event: DragEvent<HTMLElement>) {
    if (!hasDraggedFiles(event)) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = "copy";
    setIsDraggingFile(true);
  }

  function handleChatDragOver(event: DragEvent<HTMLElement>) {
    if (!hasDraggedFiles(event)) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = "copy";
    setIsDraggingFile(true);
  }

  function handleChatDragLeave(event: DragEvent<HTMLElement>) {
    if (!hasDraggedFiles(event)) {
      return;
    }

    const relatedTarget = event.relatedTarget;

    if (relatedTarget instanceof Node && event.currentTarget.contains(relatedTarget)) {
      return;
    }

    setIsDraggingFile(false);
  }

  function handleChatDrop(event: DragEvent<HTMLElement>) {
    if (!hasDraggedFiles(event)) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    setIsDraggingFile(false);

    const files = Array.from(event.dataTransfer.files ?? []);

    if (files.length > 0) {
      handleAttachFiles(files);
    }
  }

  function handleRemoveAttachment(attachmentId: string) {
    setComposerAttachments((current) =>
      current.filter((attachment) => attachment.id !== attachmentId),
    );
  }

  async function handleSubmitMessage() {
    const presetIds = composerAttachments
      .map((attachment) => attachment.serverAttachmentId)
      .filter((value): value is string => Boolean(value));
    const pendingFiles = composerAttachments
      .filter((attachment) => !attachment.serverAttachmentId)
      .map((attachment) => attachment.file);
    const attachmentPreview = composerAttachments
      .filter((attachment) => attachment.serverAttachmentId)
      .map((attachment) => ({
        id: attachment.serverAttachmentId!,
        original_filename: attachment.name,
        size_bytes: attachment.size,
        content_type: attachment.type || null,
        status: attachment.status === "indexed" ? "indexed" : "uploaded",
        parsed: attachment.status === "indexed",
        readingStatus: attachment.readingStatus,
      }));

    setComposerAttachments([]);

    await promptAndSendMessage({
      attachments: pendingFiles.length > 0 ? pendingFiles : undefined,
      attachmentIds: presetIds.length > 0 ? presetIds : undefined,
      attachmentPreview: attachmentPreview.length > 0 ? attachmentPreview : undefined,
    });
  }

  function handleDrillDown(query: string) {
    const normalized = normalizeShortcutTemplate(query.trim());

    if (!normalized) {
      return;
    }

    const promptOptions = resolveStarterPromptOptions(normalized, {});

    if (!starterRequiresShortcutModal(normalized, {})) {
      clearError();
      void sendMessageWithOperationalAgent({ content: normalized });
      return;
    }

    void promptAndSendMessage({ content: normalized }, promptOptions);
  }

  async function handleHomeStarter(query: string, context: StarterInvokeContext = {}) {
    if (shortcutPromptResolvingRef.current || isShortcutPromptOpen()) {
      return;
    }

    const normalized = normalizeShortcutTemplate(query.trim());

    if (!normalized) {
      return;
    }

    const promptOptions = resolveStarterPromptOptions(normalized, context);

    if (!starterRequiresShortcutModal(normalized, context)) {
      clearError();
      await sendMessageWithOperationalAgent({ content: normalized }, context);
      return;
    }

    shortcutPromptResolvingRef.current = true;

    try {
      const resolved = await resolveShortcutQuery(normalized, promptOptions);

      if (!resolved || hasUnresolvedShortcutPlaceholders(resolved)) {
        return;
      }

      clearError();
      await sendMessageWithOperationalAgent({ content: resolved }, context);
    } finally {
      shortcutPromptResolvingRef.current = false;
    }
  }

  async function handleHelpTryPrompt(query: string, context: StarterInvokeContext = {}) {
    const promptOptions = resolveStarterPromptOptions(query, context);

    const resolved = await resolveShortcutQuery(query, promptOptions);

    if (!resolved) {
      return;
    }

    setHelpPanelOpen(false);
    setHelpSearchQuery("");
    setDraft("");
    await sendMessageWithOperationalAgent({ content: resolved }, context);
  }

  async function handleReuseMessage(content: string) {
    const resolved = await resolveShortcutQuery(content, CHAT_SHORTCUT_PROMPT_COPY.reuse);

    if (resolved) {
      setDraft(resolved);
    }
  }

  function handleAgentIcebreaker(query: string) {
    void handleHomeStarter(query);
  }

  async function handleEditAndResendMessage(
    messageId: string,
    content: string,
    attachmentIds?: string[],
  ) {
    const resolved = await resolveShortcutQuery(content.trim(), CHAT_SHORTCUT_PROMPT_COPY.resend);

    if (!resolved) {
      return null;
    }

    return editAndResendMessage(messageId, resolved, attachmentIds);
  }

  const homeTourSteps = useMemo(
    () => homeOnboarding?.tourSteps ?? [],
    [homeOnboarding?.tourSteps],
  );

  const hasOnboardingTourSteps = homeTourSteps.length > 0;

  const canOfferOnboardingTour =
    hasOnboardingTourSteps && isConversationEmpty && !isOnboardingTourCompleted();

  const isHomeChatSurface =
    chatRoute.kind === "home" &&
    currentView === "chat" &&
    !activeAgentPageId &&
    !selectedProjectId;

  const startOnboardingTour = useCallback(() => {
    setHelpPanelOpen(false);
    setHelpSearchQuery("");
    closeMobileSidebar();

    const needsTourHomeNavigation = !isHomeChatSurface || !isConversationEmpty;

    if (needsTourHomeNavigation) {
      navigateToChatSurface(buildChatHref({ kind: "home" }));
    }

    setOnboardingTourOpen(true);
  }, [isConversationEmpty, isHomeChatSurface, navigateToChatSurface]);

  useEffect(() => {
    if (!isConversationEmpty) {
      setOnboardingTourOpen(false);
      catalogProfileSyncedRef.current = false;
      return;
    }

    let cancelled = false;

    void getAssistantCatalog({
      getAccessToken,
      agentId: helpAgentId,
      profileId: onboardingProfileId ?? undefined,
      limit: 8,
    })
      .then((payload) => {
        if (cancelled) {
          return;
        }

        setHomeHighlights(payload.contextualHighlights ?? []);
        setHomeOnboarding(payload.onboarding ?? null);
        writeHomeCatalogCache(onboardingProfileId, {
          onboarding: payload.onboarding ?? null,
          highlights: payload.contextualHighlights ?? [],
        });

        const selected = payload.onboarding?.selectedProfileId;

        if (
          selected &&
          !catalogProfileSyncedRef.current &&
          selected !== onboardingProfileId
        ) {
          catalogProfileSyncedRef.current = true;
          setOnboardingProfileId(selected);

          try {
            localStorage.setItem("minha-delpi-chat:onboarding-profile", selected);
          } catch {
            /* ignore */
          }
        }
      })
      .catch(() => {
        if (cancelled) {
          return;
        }

        setHomeHighlights([]);
        setHomeOnboarding(null);
      });

    return () => {
      cancelled = true;
    };
  }, [getAccessToken, helpAgentId, isConversationEmpty, onboardingProfileId]);

  function getComposerPlaceholder() {
    const combinedPlaceholder = formatComposerPlaceholderParts({
      projectNames: effectiveComposerProjects.map((item) => item.name),
      agentNames: effectiveComposerAgents.map((item) => item.name),
    });

    if (combinedPlaceholder) {
      if (isNarrow) {
        if (effectiveComposerProjects.length > 0 && effectiveComposerAgents.length > 0) {
          return "Chat com contexto combinado";
        }

        if (effectiveComposerProjects.length > 0) {
          return "Chat no projeto";
        }

        return "Pergunte ao agente";
      }

      return combinedPlaceholder;
    }

    return "O que vamos resolver hoje? Pode perguntar do seu jeito.";
  }

  function handleToggleContextAgent(agentId: string) {
    setRemovedComposerAgentIds((current) => removeContextId(current, agentId));
    setContextAgentIds((current) => toggleContextId(current, agentId, MAX_COMPOSER_AGENTS));
  }

  function handleToggleContextProject(projectId: string) {
    setRemovedComposerProjectIds((current) => removeContextId(current, projectId));
    setContextProjectIds((current) =>
      toggleContextId(current, projectId, MAX_COMPOSER_PROJECTS),
    );
  }

  function handleRemoveContextAgent(agentId: string) {
    setRemovedComposerAgentIds((current) =>
      toggleContextId(current, agentId, MAX_COMPOSER_AGENTS),
    );
    setContextAgentIds((current) => removeContextId(current, agentId));
  }

  function handleRemoveContextProject(projectId: string) {
    setRemovedComposerProjectIds((current) =>
      toggleContextId(current, projectId, MAX_COMPOSER_PROJECTS),
    );
    setContextProjectIds((current) => removeContextId(current, projectId));
  }

  const composerContextProps = {
    agents,
    projects,
    selectedAgentIds: contextAgentIds,
    selectedProjectIds: contextProjectIds,
    contextBarItems: composerContextBarItems,
    onToggleAgent: handleToggleContextAgent,
    onRemoveContextAgent: handleRemoveContextAgent,
    onOpenAgentPage: (agentId: string) => {
      const agent = agents.find((item) => item.id === agentId);

      if (agent) {
        navigateToChatSurface(buildChatAgentHref(agent.id));
      }
    },
    onToggleProject: handleToggleContextProject,
    onRemoveContextProject: handleRemoveContextProject,
  };

  const composerAttachmentProps = {
    attachments: composerAttachments,
    onAttachFiles: handleAttachFiles,
    onRemoveAttachment: handleRemoveAttachment,
    onClearAttachments: () => setComposerAttachments([]),
    getAccessToken,
  };

  const composerResponseModeProps = {
    showResponseModeSelector: responseModesEnabled,
    responseModes,
    responseMode,
    onResponseModeChange: setResponseMode,
  };

  const composerPresentationFormatProps = {
    showPresentationFormatSelector: true,
    presentationFormatOptions,
    presentationFormat,
    onPresentationFormatChange: setPresentationFormat,
  };

  const composerTypingCorrectionProps = {
    typingSuggestion,
    typingSuggestionLabels: typingCorrectionLabels,
    onAcceptTypingSuggestion: handleAcceptTypingSuggestion,
    onDismissTypingSuggestion: handleDismissTypingSuggestion,
  };

  const shellClassName = [
    "mdc-chat-shell",
    isDesktop && isSidebarCollapsed ? "mdc-chat-shell--sidebar-collapsed" : "",
    isLandscape ? "mdc-chat-shell--landscape" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const openAdmin =
    canOpenAdmin && onOpenAdmin
      ? (agentId?: string) => {
          const normalizedAgentId = normalizeAgentRouteId(agentId);

          if (normalizedAgentId) {
            openAdminForAgent(normalizedAgentId);
            return;
          }

          onOpenAdmin();
        }
      : undefined;

  const rootClassName = [
    "minha-delpi-chat",
    isDraggingFile ? "minha-delpi-chat--dragging" : "",
    isMobileSidebarOpen ? "minha-delpi-chat--mobile-nav-open" : "",
    isNarrow ? "minha-delpi-chat--narrow" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <main
      className={rootClassName}
      onDragEnterCapture={handleChatDragEnter}
      onDragOverCapture={handleChatDragOver}
      onDragLeaveCapture={handleChatDragLeave}
      onDropCapture={handleChatDrop}
    >
      {confirmDialog}
      {promptDialog}
      {alertDialog}
      <ChatAddContextDialog
        open={addContextDialogOpen}
        onCancel={() => setAddContextDialogOpen(false)}
        onConfirm={handleAddContextPayload}
        recentConversation={recentConversationPicks}
        getAccessToken={getAccessToken}
      />
      <ChatMemoryUsedDialog
        open={memoryUsedDialogOpen}
        usage={activeMemoryUsage}
        onClose={() => setMemoryUsedDialogOpen(false)}
      />
      {shortcutPromptDialog}
      {isDraggingFile ? (
        <div className="mdc-chat-drop-overlay" aria-hidden="true">
          <div>
            <strong>Solte o arquivo para anexar</strong>
            <span>Ele será enviado junto com a próxima pergunta.</span>
          </div>
        </div>
      ) : null}
      <section className={shellClassName}>
        {isMobileSidebarOpen ? (
          <button
            type="button"
            className="mdc-chat-sidebar-backdrop"
            aria-label="Fechar menu de conversas"
            onClick={closeMobileSidebar}
          />
        ) : null}
        <ChatSidebar
          sessions={sessions}
          archivedSessions={archivedSessions}
          agents={agents}
          projects={projects}
          activeSessionId={activeSession?.id}
          isSessionProcessing={isSessionProcessing}
          selectedProjectId={selectedProjectId}
          selectedAgentId={activeAgentPageId}
          isLoading={isLoadingSessions}
          isLoadingArchivedSessions={isLoadingArchivedSessions}
          isLoadingAgents={isLoadingAgents}
          isLoadingProjects={isLoadingProjects}
          canManageAgents={canManageAgents}
          onOpenAdmin={openAdmin}
          onNewSession={handleStartGeneralSession}
          onSelectSession={handleSelectSession}
          onRenameSession={renameSession}
          onDeleteSession={handleDeleteSession}
          onPinSession={pinSession}
          onUnpinSession={unpinSession}
          onArchiveSession={archiveSession}
          onUnarchiveSession={unarchiveSession}
          onLoadArchivedSessions={loadArchivedSessions}
          onCreateProject={addProject}
          onRenameProject={(projectId, name) => editProject(projectId, { name })}
          onDeleteProject={removeProject}
          onSelectProject={(projectId) => {
            if (!projectId) {
              navigateToChatSurface(buildChatHref({ kind: "home" }));
              return;
            }

            navigateToChatSurface(buildChatProjectHref(projectId));
          }}
          onSelectAgent={(agentId) => {
            if (!agentId) {
              navigateToChatSurface(buildChatHref({ kind: "home" }));
              return;
            }

            const agent = agents.find((item) => item.id === agentId);

            if (!agent) {
              return;
            }

            navigateToChatSurface(buildChatAgentHref(agentId));
          }}
          isCollapsed={isDesktop && isSidebarCollapsed}
          isMobileOpen={isMobileSidebarOpen}
          onCloseMobile={closeMobileSidebar}
          onToggleCollapsed={() => setIsSidebarCollapsed((current) => !current)}
          onViewChange={setCurrentView}
          onOpenAgentsDirectory={openAgentsDirectory}
          onOpenProjectsDirectory={openProjectsDirectory}
        />

        <ChatAnimatedPanel
          panelKey={currentView}
          variant="page"
          className="mdc-chat-view-host"
        >
        {currentView === "projects" ? (
          <section className="mdc-chat-main mdc-chat-main--workspace" aria-label="Projetos">
            {!isDesktop ? (
              <div className="mdc-chat-mobile-nav" role="toolbar" aria-label="Navegação">
                <button type="button" onClick={openMobileSidebar} aria-label="Abrir menu de conversas">
                  Menu
                </button>
              </div>
            ) : null}
            <ChatProjectsPage
              projects={projects}
              agents={agents}
              sessions={sessions}
              selectedProjectId={selectedProjectId}
              isLoading={isLoadingProjects}
              onBack={() => {
                clearWorkspaceError();
                navigateToChatSurface(buildChatHref({ kind: "home" }));
              }}
              onSelectProject={(projectId) => {
                clearWorkspaceError();
                navigateToChatSurface(buildChatProjectHref(projectId));
              }}
              onCreateProject={addProject}
              onRenameProject={(projectId, name) => editProject(projectId, { name })}
              onDeleteProject={removeProject}
              onConfigureProject={openProjectConfig}
            />
          </section>
        ) : currentView === "agents" ? (
          <section className="mdc-chat-main mdc-chat-main--workspace" aria-label="Gerenciar agentes">
            {!isDesktop ? (
              <div className="mdc-chat-mobile-nav" role="toolbar" aria-label="Navegação">
                <button type="button" onClick={openMobileSidebar} aria-label="Abrir menu de conversas">
                  Menu
                </button>
              </div>
            ) : null}
            <ChatAgentsPage
              agents={agents}
              selectedAgentId={activeAgentPageId}
              canManageAgents={canManageAgents}
              canManageOfficialAgents={canManageOfficialAgents}
              editAgentId={agentEditRequest?.id ?? null}
              editRequestKey={agentEditRequest?.requestKey ?? 0}
              isLoading={isLoadingAgents}
              onBack={() => {
                clearWorkspaceError();
                setAgentEditRequest(null);
                navigateToChatSurface(buildChatHref({ kind: "home" }));
              }}
              onSelectAgent={(agentId) => {
                clearWorkspaceError();
                setAgentEditRequest(null);

                if (agentId) {
                  const agent = agents.find((item) => item.id === agentId);

                  if (agent) {
                    navigateToChatSurface(buildChatAgentHref(agent.id));
                  }
                } else {
                  navigateToChatSurface(buildChatHref({ kind: "home" }));
                }
              }}
              onCreateAgent={addAgent}
              onUpdateAgent={editAgent}
              onAgentPublished={syncAgent}
              onDeleteAgent={removeAgent}
              onAgentDuplicated={() => {
                void loadAgents(false, true);
              }}
              onReloadAgents={loadAgents}
              onOpenAgentConfig={openAgentConfig}
              onCloseAgentConfig={closeAgentConfig}
              onOpenAgentSkills={openAgentSkills}
              onOpenAgentActions={openAgentActions}
              agentSubRoute={agentSubRoute}
              agentSubRouteKey={pathname}
              onOpenRagAdmin={openAdmin}
              getAccessToken={getAccessToken}
            />
          </section>
        ) : (
        <section className="mdc-chat-main" aria-label="Minha DELPI Chat">
          <ChatContextTopbar
            onOpenSidebar={isDesktop ? undefined : openMobileSidebar}
            mode={chatTopbarPresentation.topbarMode}
            title={chatTopbarPresentation.label}
            subtitle={chatTopbarPresentation.subtitle}
            badge={
              chatTopbarPresentation.topbarMode === "project" && selectedProject
                ? `${selectedProjectSessions.length} chats`
                : undefined
            }
            onOpenAdmin={openAdmin}
            onOpenHelp={() => setHelpPanelOpen(true)}
            onRenameProject={async () => {
              if (!selectedProject) {
                return;
              }

              const nextName = await prompt({
                title: "Renomear projeto",
                label: "Nome do projeto",
                defaultValue: selectedProject.name,
                placeholder: "Ex.: Qualidade, Engenharia…",
                confirmLabel: "Salvar",
              });

              if (nextName && nextName !== selectedProject.name) {
                await editProject(selectedProject.id, { name: nextName });
              }
            }}
            onOpenProjectSettings={() => {
              if (selectedProject) {
                openProjectConfig(selectedProject.id);
              }
            }}
            onDeleteProject={async () => {
              if (!selectedProject) {
                return;
              }

              const confirmed = await confirm({
                title: "Excluir projeto",
                description: `Excluir o projeto "${selectedProject.name}"?`,
                confirmLabel: "Excluir",
                cancelLabel: "Cancelar",
                danger: true,
              });

              if (!confirmed) {
                return;
              }

              const deleted = await removeProject(selectedProject.id);

              if (deleted) {
                setSelectedProjectId(null);
                clearComposerOverlayContext();
                await handleStartSession();
              }
            }}
            onManageAgents={openAgentsDirectory}
            onClearAgent={() => {
              setActiveAgentPageId(null);
              clearComposerOverlayContext();
              navigateChatHref(buildChatHref({ kind: "home" }));
              void startSession();
            }}
          />

          {error || workspaceError || unansweredTurnRecovery ? (
            <ChatInlineError
              title={
                error?.includes("diálogo dos atalhos") ||
                error?.includes("{{")
                  ? "Complete os campos antes de enviar"
                  : unansweredTurnRecovery?.title
              }
              message={
                error ||
                workspaceError ||
                unansweredTurnRecovery?.message ||
                "Tente novamente em alguns instantes."
              }
              details={error || workspaceError || undefined}
              onRetry={() => {
                const retryContent =
                  unansweredTurnRecovery?.retryContent ||
                  draft.trim() ||
                  lastSentUserText.trim();

                if (!retryContent) {
                  return;
                }

                clearError();
                dismissUnansweredTurnRecovery();
                void promptAndSendMessage({ content: retryContent });
              }}
              onDismiss={() => {
                clearWorkspaceError();
                clearError();
                dismissUnansweredTurnRecovery();
              }}
            />
          ) : null}

          {isConversationEmpty ? (
            <section className="mdc-chat-empty-composer">
              {selectedProject ? (
                <div className="mdc-chat-empty-composer__column mdc-chat-empty-composer__column--project">
                  <div className="mdc-chat-empty-composer__scroll">
                <ChatProjectHome
                  project={selectedProject}
                  sessions={selectedProjectSessions}
                  agents={agents}
                  contextAgentId={contextAgentIds[0] ?? null}
                  compact
                  settingsOpen={projectSettingsOpen}
                  onSettingsOpenChange={(open) => {
                    if (!selectedProject) {
                      return;
                    }

                    if (open) {
                      openProjectConfig(selectedProject.id);
                      return;
                    }

                    closeProjectConfig(selectedProject.id);
                  }}
                  activeSessionId={activeSession?.id}
                  isSessionProcessing={isSessionProcessing}
                  onSelectSession={handleSelectSession}
                  onRenameSession={renameSession}
                  onDeleteSession={handleDeleteSession}
                  onPinSession={pinSession}
                  onUnpinSession={unpinSession}
                  sources={projectSources[selectedProject.id] ?? []}
                  isLoadingSources={isLoadingProjectSources}
                  onUploadSource={async (file) => {
                    const source = await uploadProjectSource(selectedProject.id, file, { getAccessToken });
                    await loadProjectSources(selectedProject.id);
                    return source;
                  }}
                  onCreateTextSource={async (payload) => {
                    const source = await createProjectTextSource(selectedProject.id, payload, { getAccessToken });
                    await loadProjectSources(selectedProject.id);
                    return source;
                  }}
                  onDeleteSource={async (sourceId) => {
                    await deleteChatSource(sourceId, { getAccessToken });
                    await loadProjectSources(selectedProject.id);
                  }}
                  onDownloadSource={async (sourceId) => {
                    await downloadChatSource(sourceId, { getAccessToken });
                  }}
                  onUpdateProject={editProject}
                  getAccessToken={getAccessToken}
                  onUseAgent={handleToggleContextAgent}
                  onOpenAgentPage={(agentId) => {
                    const agent = agents.find((item) => item.id === agentId);

                    setCanvasDocument(null);
                    setSelectedProjectId(null);
                    clearComposerOverlayContext();
                    setActiveAgentPageId(agentId);
                    setCurrentView("chat");

                    if (agent) {
                      navigateChatHref(buildChatAgentHref(agent.id));
                    }

                    void startSession();
                  }}
                  onSetDefaultAgent={async (agentId) => {
                    const updated = await editProject(selectedProject.id, {
                      defaultAgentId: agentId,
                    });

                    return updated;
                  }}
                  onDeleteProject={async (projectId) => {
                    const deleted = await removeProject(projectId);

                    if (deleted) {
                      setSelectedProjectId(null);
                      clearComposerOverlayContext();
                      await handleStartSession();
                    }

                    return deleted;
                  }}
                  onClearProject={() => {
                    setSelectedProjectId(null);
                    clearComposerOverlayContext();
                    navigateChatHref(buildChatHref({ kind: "home" }));
                    void handleStartSession();
                  }}
                  composer={
                    <ChatInput
                      value={draft}
                      disabled={false}
                      isSending={isStreamingActiveSession}
                      variant="center"
                      placeholder={getComposerPlaceholder()}
                      {...composerAttachmentProps}
                      {...composerPresentationFormatProps}
                      {...composerPresentationFormatProps}
                    {...composerPresentationFormatProps}
                      {...composerResponseModeProps}
                      {...composerContextProps}
                      {...composerTypingCorrectionProps}
                      onChange={setDraft}
                      onSubmit={handleSubmitMessage}
                      onCancel={cancelStreaming}
                    />
                  }
                />
                  </div>
                </div>
              ) : (
                <div className="mdc-chat-empty-composer__column">
                  <div className="mdc-chat-empty-composer__scroll">
                    {activeAgentPage ? (
                      <ChatAgentHome
                        agent={activeAgentPage}
                        onUseSuggestion={(query) => {
                          void handleAgentIcebreaker(query);
                        }}
                        canManageAgent={canManageAgents}
                        onManageAgent={() => {
                          if (!canManageAgents || !activeAgentPage?.id) {
                            return;
                          }

                          setAgentEditRequest({
                            id: activeAgentPage.id,
                            requestKey: Date.now(),
                          });
                          setCurrentView("agents");
                          navigateChatHref(buildChatAgentConfigHref(activeAgentPage.id));
                        }}
                      />
                    ) : (
                      <>
                        <ChatEmptyState
                          displayName={userDisplayName}
                          contextualHighlights={homeHighlights}
                          onUseStarter={handleHomeStarter}
                          onStartTour={
                            canOfferOnboardingTour ? startOnboardingTour : undefined
                          }
                        />

                        {onboardingTourOpen && homeTourSteps.length > 0 ? (
                          <ChatOnboardingTour
                            autoStart
                            steps={homeTourSteps}
                            onDemoQuery={setDraft}
                            onPlusMenuOpen={setTourPlusMenuOpen}
                            onDismiss={() => {
                              setOnboardingTourOpen(false);
                              setTourPlusMenuOpen(null);
                            }}
                          />
                        ) : null}
                      </>
                    )}
                  </div>

                  <ChatInput
                    value={draft}
                    disabled={false}
                    isSending={isStreamingActiveSession}
                    variant="center"
                    placeholder={getComposerPlaceholder()}
                    {...composerAttachmentProps}
                    {...composerPresentationFormatProps}
                    {...composerPresentationFormatProps}
                  {...composerResponseModeProps}
                    {...composerContextProps}
                    {...composerTypingCorrectionProps}
                    plusMenuOpen={tourPlusMenuOpen ?? undefined}
                    onPlusMenuOpenChange={setTourPlusMenuOpen}
                    onChange={setDraft}
                    onSubmit={handleSubmitMessage}
                    onCancel={cancelStreaming}
                  />
                </div>
              )}
            </section>
          ) : (
            <section className="mdc-chat-conversation" aria-label="Conversa">
              <ChatMessageList
                messages={messages}
                conversationKey={activeSession?.id ?? null}
                streamingAnswer={streamingAnswer}
                streamingSources={streamingSources}
                streamingToolCalls={streamingToolCalls}
                streamingAdminDebug={streamingAdminDebug}
                streamingStatus={streamingStatus}
                streamingActivityLog={streamingActivityLog}
                streamingShowPresentation={streamingShowPresentation}
                streamingCanvasOpen={streamingCanvasOpen}
                isStreaming={isStreamingActiveSession}
                isPlaybackActive={isPlaybackActive}
                isLoading={isLoadingMessages && messages.length === 0}
                onEditAndResendMessage={handleEditAndResendMessage}
                sessionId={activeSession?.id ?? null}
                onSwitchMessageBranch={switchMessageBranch}
                branchSwitchingMessageId={branchSwitchingMessageId}
                onContinueFromMessage={continueFromMessage}
                onReuseMessage={(content) => {
                  void handleReuseMessage(content);
                }}
                onDrillDown={handleDrillDown}
                onAddMessageToContext={
                  activeSession?.id ? handleAddMessageToContext : undefined
                }
                onAddMessageTurnToContext={
                  activeSession?.id ? handleAddMessageTurnToContext : undefined
                }
                onRecordHelpEvent={(payload) => {
                  void recordAssistantHelpEvent(
                    {
                      ...payload,
                      metadata: {
                        ...(payload.metadata ?? {}),
                        sessionId:
                          payload.metadata?.sessionId ??
                          activeSession?.id ??
                          null,
                      },
                    },
                    { getAccessToken },
                  ).catch(() => {
                    /* telemetria opcional — não bloquear chips/modal */
                  });
                }}
                onMessageFeedback={setMessageFeedback}
                getAccessToken={getAccessToken}
                onDownloadAttachment={async (attachmentId) => {
                  await downloadChatAttachment(attachmentId, { getAccessToken });
                }}
                onOpenCanvas={openCanvasPanel}
                lastSentUserText={lastSentUserText}
              />

              <div className="mdc-chat-composer-footer">
                <ChatContextBar
                  chips={activeContextChips}
                  summary={activeContextSummary}
                  preferenceHint={activePreferenceHint}
                  onClearContext={handleClearActiveContext}
                  onDismissChip={handleDismissContextChip}
                  onChipAction={handleDrillDown}
                  onAddContext={() => setAddContextDialogOpen(true)}
                  onViewMemory={handleViewMemoryUsed}
                  onPinChip={handlePinContextChip}
                />

                <ChatInput
                  value={draft}
                  disabled={false}
                  isSending={isStreamingActiveSession}
                  variant="dock"
                  placeholder={getComposerPlaceholder()}
                  {...composerAttachmentProps}
                  {...composerPresentationFormatProps}
                  {...composerResponseModeProps}
                  {...composerContextProps}
                  {...composerTypingCorrectionProps}
                  onChange={setDraft}
                  onSubmit={handleSubmitMessage}
                  onCancel={cancelStreaming}
                />
              </div>
            </section>
          )}
        </section>
        )}
          <div id="mdc-modal-root" className="mdc-modal-root" aria-hidden="true" />
        </ChatAnimatedPanel>

        <ChatCanvas
          document={canvasDocument}
          onChange={setCanvasDocument}
          onSave={saveCanvasDocument}
          onClose={() => setCanvasDocument(null)}
        />

        <ChatHelpPanel
          open={helpPanelOpen}
          catalog={helpCatalog}
          loading={helpCatalogLoading}
          error={helpCatalogError}
          searchQuery={helpSearchQuery}
          onSearchQueryChange={setHelpSearchQuery}
          onClose={() => {
            setHelpPanelOpen(false);
            setHelpSearchQuery("");
          }}
          onTryPrompt={(query, context) => {
            void handleHelpTryPrompt(query, context);
          }}
          onStartTour={hasOnboardingTourSteps ? startOnboardingTour : undefined}
        />
      </section>
    </main>
  );
}
