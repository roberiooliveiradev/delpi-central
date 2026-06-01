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
import { ChatInput, type ChatInputAttachment } from "../components/ChatInput";
import { ChatInlineError } from "../components/ChatInlineError";
import { ChatContextBar, type ChatContextChip } from "../components/ChatContextBar";
import { ChatMessageList } from "../components/ChatMessageList";
import { ChatContextTopbar } from "../components/ChatContextTopbar";
import { ChatHelpPanel } from "../components/ChatHelpPanel";
import { ChatAnimatedPanel } from "../components/ChatAnimatedPanel";
import { ChatProjectHome } from "../components/ChatProjectHome";
import { ChatSidebar, type ChatSidebarView } from "../components/ChatSidebar";
import { useConfirmDialog } from "../components/useConfirmDialog";
import {
  useChatShortcutPrompt,
  type ShortcutPromptOptions,
} from "../hooks/useChatShortcutPrompt";
import {
  buildActiveContextSummary,
  collectActiveContextChips,
  contextChipKey,
  extractActivePreferenceHint,
} from "../chatActiveContext";
import {
  CHAT_SHORTCUT_PROMPT_COPY,
  extractProductCodeFromContextChips,
  hasUnresolvedShortcutPlaceholders,
  hasShortcutPlaceholders,
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
  clearChatSessionMemory,
  createChatArtifact,
  createProjectTextSource,
  deleteChatSource,
  downloadChatAttachment,
  downloadChatSource,
  getAssistantCatalog,
  getChatCapabilities,
  recordAssistantHelpEvent,
  listProjectSources,
  updateChatArtifact,
  uploadChatAttachment,
  uploadProjectSource,
} from "../../data/api/chatApi";
import { mapApiAttachmentToComposerStatus } from "../chatAttachmentStatus";
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
import { navigateChatHref } from "../../navigation/chatNavigation";
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
} from "../../data/api/chatTypes";
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

  const [contextAgentId, setContextAgentId] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<ChatSidebarView>(() =>
    initialRoute ? getChatSidebarViewForRoute(initialRoute) : "chat",
  );
  const chatRoute = useMemo(() => parseChatRoute(pathname), [pathname]);
  const [userDisplayName, setUserDisplayName] = useState<string | null>(null);
  const [composerAttachments, setComposerAttachments] = useState<ChatInputAttachment[]>([]);
  const [projectSources, setProjectSources] = useState<Record<string, import("../../data/api/chatTypes").ChatWorkspaceSource[]>>({});
  const [isLoadingProjectSources, setIsLoadingProjectSources] = useState(false);
  const [isDraggingFile, setIsDraggingFile] = useState(false);
  const requestedAgentId = activeAgentPageId ?? contextAgentId ?? null;
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
  const [homeCatalogLoading, setHomeCatalogLoading] = useState(
    () => !initialHomeCatalogCache?.onboarding,
  );
  const [homeCatalogError, setHomeCatalogError] = useState(false);
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
    projectId: selectedProjectId,
    agentId: requestedAgentId,
    onSessionActivated: (sessionId, context) => {
      const agentId = context?.agentId ?? requestedAgentId;
      const projectId = context?.projectId ?? selectedProjectId;

      if (agentId) {
        navigateChatHref(buildChatAgentSessionHref(agentId, sessionId), { replace: true });
        return;
      }

      if (projectId) {
        navigateChatHref(buildChatProjectSessionHref(projectId, sessionId), { replace: true });
        return;
      }

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

  const [contextMemoryCleared, setContextMemoryCleared] = useState(false);
  const [dismissedContextChipKeys, setDismissedContextChipKeys] = useState<string[]>([]);

  const mergedContextChips = useMemo(() => {
    if (contextMemoryCleared) {
      return [];
    }

    return collectActiveContextChips(messages);
  }, [messages, contextMemoryCleared]);

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

  const activePreferenceHint = useMemo(
    () => extractActivePreferenceHint(activeContextChips),
    [activeContextChips],
  );

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

        await sendMessage({ ...params, content: recovered });
        return;
      }

      await sendMessage({ ...params, content: resolved });
    },
    [clearError, draft, resolveShortcutQuery, sendMessage, setDraft, shortcutSendPromptOptions],
  );

  useEffect(() => {
    promptAndSendMessageRef.current = promptAndSendMessage;
    isShortcutPromptOpenRef.current = isShortcutPromptOpen;
    resolveShortcutQueryRef.current = resolveShortcutQuery;
    shortcutSendPromptOptionsRef.current = shortcutSendPromptOptions;
  }, [isShortcutPromptOpen, promptAndSendMessage, resolveShortcutQuery, shortcutSendPromptOptions]);

  useEffect(() => {
    setContextMemoryCleared(false);
    setDismissedContextChipKeys([]);
  }, [activeSession?.id]);

  const handleDismissContextChip = useCallback((chip: ChatContextChip) => {
    const key = contextChipKey(chip);

    setDismissedContextChipKeys((current) =>
      current.includes(key) ? current : [...current, key],
    );
  }, []);

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
  const conversationAgent = agents.find((agent) => agent.id === conversationAgentId);
  const contextAgent = agents.find((agent) => agent.id === contextAgentId);
  const helpAgentId = contextAgentId ?? conversationAgentId ?? activeAgentPageId ?? undefined;

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

  function getProjectDefaultAgentId(projectId: string | null): string | null {
    if (!projectId) {
      return null;
    }

    return projects.find((project) => project.id === projectId)?.default_agent_id ?? null;
  }

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
          setContextAgentId(null);
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
          setContextAgentId(null);
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
            setContextAgentId(session.agent_id ?? getProjectDefaultAgentId(routeProject.id));
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
          setContextAgentId(getProjectDefaultAgentId(routeProject.id));
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
            setContextAgentId(null);
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
          setContextAgentId(null);
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
          setContextAgentId(getProjectDefaultAgentId(routeProject.id));
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
          setContextAgentId(null);
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
        }
      } catch {
        if (isMounted) {
          setCanManageAgents(false);
          setCanManageOfficialAgents(false);
          setCanOpenAdmin(false);
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

  async function handleStartGeneralSession() {
    navigateChatHref(buildChatHref({ kind: "home" }));
  }

  function handleSelectSession(session: typeof sessions[number]) {
    clearWorkspaceError();
    clearError();
    setCanvasDocument(null);
    setComposerAttachments([]);
    setSelectedProjectId(session.project_id ?? null);
    setActiveAgentPageId(session.agent_id ?? null);
    setContextAgentId(null);
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
        const metadata = uploaded.metadata as Record<string, unknown> | null;
        const readingStatus =
          typeof metadata?.readingStatus === "string" ? metadata.readingStatus : undefined;

        setComposerAttachments((current) =>
          current.map((item) =>
            item.id === localId
              ? {
                  ...item,
                  status: mapApiAttachmentToComposerStatus(uploaded.status),
                  serverAttachmentId: uploaded.id,
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
      window.alert("Arquivos vazios não podem ser anexados.");
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
    void promptAndSendMessage(
      { content: query },
      resolveStarterPromptOptions(query, {}),
    );
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
      await sendMessage({ content: normalized });
      return;
    }

    shortcutPromptResolvingRef.current = true;

    try {
      const resolved = await resolveShortcutQuery(normalized, promptOptions);

      if (!resolved || hasUnresolvedShortcutPlaceholders(resolved)) {
        return;
      }

      clearError();
      await sendMessage({ content: resolved });
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
    await sendMessage({ content: resolved });
  }

  async function handleReuseMessage(content: string) {
    const resolved = await resolveShortcutQuery(content, CHAT_SHORTCUT_PROMPT_COPY.reuse);

    if (resolved) {
      setDraft(resolved);
    }
  }

  async function handleInsertQuery(query: string) {
    const promptOptions = hasShortcutPlaceholders(query)
      ? resolveStarterPromptOptions(query, {})
      : CHAT_SHORTCUT_PROMPT_COPY.insert;

    const resolved = await resolveShortcutQuery(query, promptOptions);

    if (resolved) {
      setDraft(resolved);
    }
  }

  function handleAgentIcebreaker(query: string) {
    void handleHomeStarter(query);
  }

  async function handleEditAndResendMessage(messageId: string, content: string) {
    const resolved = await resolveShortcutQuery(content.trim(), CHAT_SHORTCUT_PROMPT_COPY.resend);

    if (!resolved) {
      return null;
    }

    return editAndResendMessage(messageId, resolved);
  }

  const hasActiveConversation =
    messages.length > 0 ||
    isStreamingActiveSession ||
    (isStreamingActiveSession && Boolean(streamingAnswer));

  const isConversationEmpty = !hasActiveConversation;

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
      navigateChatHref(buildChatHref({ kind: "home" }));
      applyChatRoute({ kind: "home" });
    }

    setOnboardingTourOpen(true);
  }, [
    applyChatRoute,
    isConversationEmpty,
    isHomeChatSurface,
  ]);

  useEffect(() => {
    if (!isConversationEmpty) {
      setOnboardingTourOpen(false);
      catalogProfileSyncedRef.current = false;
      return;
    }

    setHomeCatalogLoading(true);
  }, [isConversationEmpty]);

  useEffect(() => {
    if (!isConversationEmpty) {
      setHomeCatalogLoading(false);
      return;
    }

    let cancelled = false;

    setHomeCatalogLoading(true);
    setHomeCatalogError(false);

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
        setHomeCatalogError(true);
      })
      .finally(() => {
        if (!cancelled) {
          setHomeCatalogLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [getAccessToken, helpAgentId, isConversationEmpty, onboardingProfileId]);

  function handleSelectOnboardingProfile(profileId: string) {
    setOnboardingProfileId(profileId);

    const cached = readHomeCatalogCache(profileId);

    if (cached?.onboarding) {
      setHomeOnboarding(cached.onboarding);
      setHomeHighlights(cached.highlights ?? []);
    }

    try {
      localStorage.setItem("minha-delpi-chat:onboarding-profile", profileId);
    } catch {
      /* ignore */
    }
  }

  function getComposerPlaceholder() {
    if (isNarrow) {
      if (selectedProject && contextAgent) {
        return `Chat em ${selectedProject.name}`;
      }

      if (selectedProject) {
        return `Chat no projeto`;
      }

      if (contextAgent || conversationAgent) {
        return "Pergunte ao agente";
      }

      return "Pergunte algo";
    }

    if (selectedProject && contextAgent) {
      return `Pergunte sobre ${selectedProject.name} com ${contextAgent.name}`;
    }

    if (selectedProject) {
      return `Pergunte sobre ${selectedProject.name} ou envie um arquivo`;
    }

    if (contextAgent) {
      return `Código, descrição ou pergunta — ${contextAgent.name} consulta dados autorizados`;
    }

    if (conversationAgent) {
      return `Pergunte ao agente ${conversationAgent.name}`;
    }

    if (activeAgentPage) {
      return `Converse com ${activeAgentPage.name} — código, descrição ou pergunta`;
    }

    return "O que vamos resolver hoje? Pode perguntar do seu jeito.";
  }

  async function handleSelectContextAgent(agentId: string | null) {
    setContextAgentId(agentId);
  }

  async function handleSelectContextProject(projectId: string | null) {
    setSelectedProjectId(projectId);
    setActiveAgentPageId(null);
    setContextAgentId(getProjectDefaultAgentId(projectId));
  }

  const composerContextProps = {
    agents,
    projects,
    selectedAgentId: contextAgentId,
    selectedProjectId,
    onSelectAgent: handleSelectContextAgent,
    onOpenAgentPage: (agentId: string) => {
      const agent = agents.find((item) => item.id === agentId);

      setCanvasDocument(null);
      setSelectedProjectId(null);
      setContextAgentId(null);
      setActiveAgentPageId(agentId);
      setCurrentView("chat");

      if (agent) {
        navigateChatHref(buildChatAgentHref(agent.id));
      }

      void startSession();
    },
    onSelectProject: handleSelectContextProject,
  };

  const agentPageComposerContextProps = {
    agents: [],
    projects: [],
    selectedAgentId: null,
    selectedProjectId: null,
    onSelectAgent: () => undefined,
    onSelectProject: () => undefined,
  };

  const composerAttachmentProps = {
    attachments: composerAttachments,
    onAttachFiles: handleAttachFiles,
    onRemoveAttachment: handleRemoveAttachment,
    onClearAttachments: () => setComposerAttachments([]),
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
              navigateChatHref(buildChatHref({ kind: "home" }));
              return;
            }

            navigateChatHref(buildChatProjectHref(projectId));
          }}
          onSelectAgent={(agentId) => {
            if (!agentId) {
              navigateChatHref(buildChatHref({ kind: "home" }));
              return;
            }

            const agent = agents.find((item) => item.id === agentId);

            if (!agent) {
              return;
            }

            navigateChatHref(buildChatAgentHref(agentId));
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
                setCurrentView("chat");
                navigateChatHref(buildChatHref({ kind: "home" }));
              }}
              onSelectProject={(projectId) => {
                clearWorkspaceError();
                clearError();
                setCanvasDocument(null);
                setActiveAgentPageId(null);
                setContextAgentId(null);
                setSelectedProjectId(projectId);
                setCurrentView("chat");
                navigateChatHref(buildChatProjectHref(projectId));
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
                setCurrentView("chat");
                navigateChatHref(buildChatHref({ kind: "home" }));
              }}
              onSelectAgent={(agentId) => {
                clearWorkspaceError();
                clearError();
                setCanvasDocument(null);
                setSelectedProjectId(null);
                setAgentEditRequest(null);
                setActiveAgentPageId(agentId);
                setContextAgentId(null);
                setCurrentView("chat");

                if (agentId) {
                  const agent = agents.find((item) => item.id === agentId);

                  if (agent) {
                    navigateChatHref(buildChatAgentHref(agent.id));
                  }
                } else {
                  navigateChatHref(buildChatHref({ kind: "home" }));
                }

                void startSession();
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
            mode={selectedProject ? "project" : conversationAgent ? "agent" : "general"}
            title={
              selectedProject?.name ||
              conversationAgent?.name ||
              "Minha DELPI Chat"
            }
            subtitle={
              selectedProject
                ? contextAgent
                  ? `Projeto usando ${contextAgent.name}`
                  : "Projeto selecionado"
                : conversationAgent
                  ? "Conversa do agente"
                  : contextAgent
                    ? `Chat usando ${contextAgent.name}`
                    : "Assistente corporativo"
            }
            badge={
              selectedProject
                ? `${selectedProjectSessions.length} chats`
                : undefined
            }
            onOpenAdmin={openAdmin}
            onOpenHelp={() => setHelpPanelOpen(true)}
            onRenameProject={async () => {
              if (!selectedProject) {
                return;
              }

              const nextName = window.prompt(
                "Novo nome do projeto",
                selectedProject.name,
              )?.trim();

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
                setContextAgentId(null);
                await handleStartSession();
              }
            }}
            onManageAgents={canManageAgents ? openAgentsDirectory : undefined}
            onClearAgent={() => {
              setActiveAgentPageId(null);
              setContextAgentId(null);
              navigateChatHref(buildChatHref({ kind: "home" }));
              void startSession();
            }}
          />

          {error || workspaceError ? (
            <ChatInlineError
              title={
                error?.includes("diálogo dos atalhos") ||
                error?.includes("{{")
                  ? "Complete os campos antes de enviar"
                  : undefined
              }
              message={
                error ||
                workspaceError ||
                "Tente novamente em alguns instantes."
              }
              details={error || workspaceError}
              onRetry={() => {
                if (draft.trim()) {
                  void handleSubmitMessage();
                  return;
                }

                if (lastSentUserText.trim()) {
                  void promptAndSendMessage({ content: lastSentUserText.trim() });
                }
              }}
              onDismiss={() => {
                clearWorkspaceError();
                clearError();
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
                  contextAgentId={contextAgentId}
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
                  onUseAgent={handleSelectContextAgent}
                  onOpenAgentPage={(agentId) => {
                    const agent = agents.find((item) => item.id === agentId);

                    setCanvasDocument(null);
                    setSelectedProjectId(null);
                    setContextAgentId(null);
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

                    if (updated) {
                      setContextAgentId(agentId);
                    }

                    return updated;
                  }}
                  onDeleteProject={async (projectId) => {
                    const deleted = await removeProject(projectId);

                    if (deleted) {
                      setSelectedProjectId(null);
                      setContextAgentId(null);
                      await handleStartSession();
                    }

                    return deleted;
                  }}
                  onClearProject={() => {
                    setSelectedProjectId(null);
                    setContextAgentId(null);
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
                      {...composerContextProps}
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
                          onboarding={homeOnboarding}
                          catalogLoading={homeCatalogLoading}
                          catalogError={homeCatalogError}
                          selectedProfileId={onboardingProfileId}
                          onSelectProfile={handleSelectOnboardingProfile}
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
                    {...(activeAgentPage ? agentPageComposerContextProps : composerContextProps)}
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
                onSwitchMessageBranch={switchMessageBranch}
                branchSwitchingMessageId={branchSwitchingMessageId}
                onContinueFromMessage={continueFromMessage}
                onReuseMessage={(content) => {
                  void handleReuseMessage(content);
                }}
                onDrillDown={handleDrillDown}
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
                  );
                }}
                onMessageFeedback={setMessageFeedback}
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
                />

                <ChatInput
                  value={draft}
                  disabled={false}
                  isSending={isStreamingActiveSession}
                  variant="dock"
                  placeholder={getComposerPlaceholder()}
                  {...composerAttachmentProps}
                  {...composerContextProps}
                  onChange={setDraft}
                  onSubmit={handleSubmitMessage}
                  onCancel={cancelStreaming}
                  onInsertQuery={(query) => {
                    void handleInsertQuery(query);
                  }}
                />
              </div>
            </section>
          )}
        </section>
        )}
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
