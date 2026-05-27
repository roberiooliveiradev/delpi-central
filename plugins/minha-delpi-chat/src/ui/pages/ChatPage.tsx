import { type DragEvent, useCallback, useEffect, useState } from "react";
import { ChatCanvas, type ChatCanvasDocument } from "../components/ChatCanvas";
import { ChatAgentHome } from "../components/ChatAgentHome";
import { ChatEmptyState } from "../components/ChatEmptyState";
import "./ChatPage.css";
import "../layout/chat-layout.css";
import { useChatLayout } from "../../state/hooks/useChatLayout";
import { ChatInput, type ChatInputAttachment } from "../components/ChatInput";
import { ChatInlineError } from "../components/ChatInlineError";
import { ChatMessageList } from "../components/ChatMessageList";
import { ChatContextTopbar } from "../components/ChatContextTopbar";
import { ChatAnimatedPanel } from "../components/ChatAnimatedPanel";
import { ChatProjectHome } from "../components/ChatProjectHome";
import { ChatSidebar, type ChatSidebarView } from "../components/ChatSidebar";
import { ChatAgentsPage } from "./ChatAgentsPage";
import { ChatProjectsPage } from "./ChatProjectsPage";
import {
  createChatArtifact,
  createProjectTextSource,
  deleteChatSource,
  getChatCapabilities,
  listProjectSources,
  updateChatArtifact,
  uploadProjectSource,
} from "../../data/api/chatApi";
import {
  buildChatHref,
  buildChatProjectHref,
  buildChatSessionHref,
  type ChatRoute,
} from "../../navigation/chatRoutes";
import { navigateChatHref } from "../../navigation/chatNavigation";
import { useChatRouteSync } from "../../state/hooks/useChatRouteSync";
import { useChatSession } from "../../state/hooks/useChatSession";
import { useChatWorkspace } from "../../state/hooks/useChatWorkspace";
import { getDisplayNameFromAccessToken } from "../../utils/authDisplayName";

const SIDEBAR_COLLAPSED_STORAGE_KEY = "minha-delpi-chat.sidebar-collapsed";


function getAgentIcebreakerCount(agent: { metadata: Record<string, unknown> | null } | null | undefined): number {
  const value = agent?.metadata?.icebreakers;

  if (!Array.isArray(value)) {
    return 0;
  }

  return value.filter((item) => typeof item === "string" && item.trim()).length;
}

type ChatPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  pathname?: string;
  initialRoute?: ChatRoute;
  onOpenAdmin?: (agentId?: string) => void;
};


export function ChatPage({
  getAccessToken,
  pathname,
  onOpenAdmin,
}: ChatPageProps) {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [activeAgentPageKey, setActiveAgentPageKey] = useState<string | null>(null);
  const [agentEditRequest, setAgentEditRequest] = useState<{
    key: string;
    requestKey: number;
  } | null>(null);
  const [canManageAgents, setCanManageAgents] = useState(false);
  const [canManageOfficialAgents, setCanManageOfficialAgents] = useState(false);
  const [hasLoadedManageAgentsPermission, setHasLoadedManageAgentsPermission] = useState(false);
  const [canOpenAdmin, setCanOpenAdmin] = useState(false);

  const [contextAgentKey, setContextAgentKey] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<ChatSidebarView>("chat");
  const [projectSettingsRequestKey, setProjectSettingsRequestKey] = useState(0);
  const [userDisplayName, setUserDisplayName] = useState<string | null>(null);
  const [composerAttachments, setComposerAttachments] = useState<ChatInputAttachment[]>([]);
  const [projectSources, setProjectSources] = useState<Record<string, import("../../data/api/chatTypes").ChatWorkspaceSource[]>>({});
  const [isLoadingProjectSources, setIsLoadingProjectSources] = useState(false);
  const [isDraggingFile, setIsDraggingFile] = useState(false);

  const requestedAgentKey = activeAgentPageKey ?? contextAgentKey ?? null;

  const {
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
    isComposerBusy,
    isStreamingActiveSession,
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
    reuseMessage,
    setMessageFeedback,
  } = useChatSession({
    getAccessToken,
    projectId: selectedProjectId,
    agentKey: requestedAgentKey,
    onSessionActivated: (sessionId) => {
      navigateChatHref(buildChatSessionHref(sessionId), { replace: true });
    },
  });

  const {
    agents,
    projects,
    isLoadingAgents,
    isLoadingProjects,
    workspaceError,
    clearWorkspaceError,
    addAgent,
    editAgent,
    removeAgent,
    addProject,
    editProject,
    removeProject,
    loadAgents,
  } = useChatWorkspace({ getAccessToken });

  const [canvasDocument, setCanvasDocument] = useState<ChatCanvasDocument | null>(null);
  const selectedProject = projects.find((project) => project.id === selectedProjectId);
  const activeAgentPage = agents.find((agent) => agent.key === activeAgentPageKey);
  const conversationAgentKey = activeSession?.agent_key ?? activeAgentPageKey;
  const conversationAgent = agents.find((agent) => agent.key === conversationAgentKey);
  const contextAgent = agents.find((agent) => agent.key === contextAgentKey);
  const selectedProjectSessions = selectedProjectId
    ? sessions.filter((session) => session.project_id === selectedProjectId)
    : [];

  function getProjectDefaultAgentKey(projectId: string | null): string | null {
    if (!projectId) {
      return null;
    }

    return projects.find((project) => project.id === projectId)?.default_agent_key ?? null;
  }

  const { isDesktop, isLandscape } = useChatLayout();
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    return localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY) === "true";
  });

  function closeMobileSidebar() {
    setIsMobileSidebarOpen(false);
  }

  const applyChatRoute = useCallback(
    (route: ChatRoute) => {
      const hasOutboundInFlight =
        messages.some((message) => message.metadata?.optimistic === true) ||
        Boolean(streamingStatus) ||
        isStreamingActiveSession;

      const shouldPreserveAgentCompose =
        route.kind === "agent" &&
        hasOutboundInFlight &&
        activeAgentPageKey === route.agentKey;

      const shouldPreserveProjectCompose =
        route.kind === "project" &&
        hasOutboundInFlight &&
        selectedProjectId === route.projectId &&
        (!activeSession || activeSession.project_id === route.projectId);

      switch (route.kind) {
        case "home": {
          if (
            !activeSession &&
            !selectedProjectId &&
            !activeAgentPageKey &&
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
          setActiveAgentPageKey(null);
          setContextAgentKey(null);
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
          setActiveAgentPageKey(null);
          setContextAgentKey(null);
          setCurrentView("chat");
          selectSession(session);
          closeMobileSidebar();
          break;
        }
        case "project": {
          if (shouldPreserveProjectCompose) {
            closeMobileSidebar();
            return;
          }

          if (selectedProjectId === route.projectId && !activeSession) {
            closeMobileSidebar();
            return;
          }

          clearWorkspaceError();
          clearError();
          setCanvasDocument(null);
          setComposerAttachments([]);
          setSelectedProjectId(route.projectId);
          setActiveAgentPageKey(null);
          setContextAgentKey(getProjectDefaultAgentKey(route.projectId));
          setCurrentView("chat");
          void startSession();
          closeMobileSidebar();
          break;
        }
        case "agent": {
          if (shouldPreserveAgentCompose) {
            closeMobileSidebar();
            return;
          }

          if (activeAgentPageKey === route.agentKey && !activeSession) {
            closeMobileSidebar();
            return;
          }

          clearWorkspaceError();
          clearError();
          setCanvasDocument(null);
          setComposerAttachments([]);
          setSelectedProjectId(null);
          setActiveAgentPageKey(route.agentKey);
          setContextAgentKey(null);
          setCurrentView("chat");
          void startSession();
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
      activeAgentPageKey,
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
    ],
  );

  useChatRouteSync({
    pathname,
    sessions,
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
    setActiveAgentPageKey(null);
    setContextAgentKey(null);
    setCurrentView("chat");
    selectSession(session);
    closeMobileSidebar();
  }

  async function handleDeleteSession(sessionId: string) {
    setCanvasDocument(null);
    return deleteSession(sessionId);
  }

  function handleAttachFiles(files: File[]) {
    const validFiles = files.filter((file) => file.size > 0);

    if (validFiles.length < files.length) {
      window.alert("Arquivos vazios não podem ser anexados.");
    }

    const nextAttachments = validFiles.map((file) => ({
      id: `${file.name}-${file.size}-${file.lastModified}-${crypto.randomUUID()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      file,
    }));

    if (nextAttachments.length === 0) {
      return;
    }

    setComposerAttachments((current) => [...current, ...nextAttachments].slice(0, 10));
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
    const messageToSend = draft.trim();
    const files = composerAttachments.map((attachment) => attachment.file);

    if (!messageToSend) {
      return;
    }

    setComposerAttachments([]);

    await sendMessage({ attachments: files });
  }

  const hasActiveConversation =
    messages.length > 0 ||
    isStreamingActiveSession ||
    (isStreamingActiveSession && Boolean(streamingAnswer));

  const isConversationEmpty = !hasActiveConversation;

  function getComposerPlaceholder() {
    if (selectedProject && contextAgent) {
      return `Novo chat em ${selectedProject.name} usando ${contextAgent.name}`;
    }

    if (selectedProject) {
      return `Novo chat em ${selectedProject.name}`;
    }

    if (contextAgent) {
      return `Pergunte usando ${contextAgent.name}`;
    }

    if (conversationAgent) {
      return `Pergunte ao agente ${conversationAgent.name}`;
    }

    return "Pergunte alguma coisa";
  }

  async function handleSelectContextAgent(agentKey: string | null) {
    setContextAgentKey(agentKey);
  }

  async function handleSelectContextProject(projectId: string | null) {
    setSelectedProjectId(projectId);
    setActiveAgentPageKey(null);
    setContextAgentKey(getProjectDefaultAgentKey(projectId));
  }

  const composerContextProps = {
    agents,
    projects,
    selectedAgentKey: contextAgentKey,
    selectedProjectId,
    onSelectAgent: handleSelectContextAgent,
    onOpenAgentPage: (agentKey: string) => {
      setCanvasDocument(null);
      setSelectedProjectId(null);
      setContextAgentKey(null);
      setActiveAgentPageKey(agentKey);
      setCurrentView("chat");
      void startSession();
    },
    onSelectProject: handleSelectContextProject,
  };

  const agentPageComposerContextProps = {
    agents: [],
    projects: [],
    selectedAgentKey: null,
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

  const openAdmin = canOpenAdmin && onOpenAdmin ? () => onOpenAdmin() : undefined;

  const rootClassName = [
    "minha-delpi-chat",
    isDraggingFile ? "minha-delpi-chat--dragging" : "",
    isMobileSidebarOpen ? "minha-delpi-chat--mobile-nav-open" : "",
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
          selectedAgentKey={activeAgentPageKey}
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
          onSelectAgent={(agentKey) => {
            if (!agentKey) {
              navigateChatHref(buildChatHref({ kind: "home" }));
              return;
            }

            navigateChatHref(buildChatHref({ kind: "agent", agentKey }));
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
          <section className="mdc-chat-main" aria-label="Projetos">
            {!isDesktop ? (
              <div className="mdc-chat-mobile-nav" role="toolbar" aria-label="Navegação">
                <button type="button" onClick={openMobileSidebar} aria-label="Abrir menu de conversas">
                  Menu
                </button>
              </div>
            ) : null}
            <ChatProjectsPage
              projects={projects}
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
                setActiveAgentPageKey(null);
                setContextAgentKey(null);
                setSelectedProjectId(projectId);
                setCurrentView("chat");
                navigateChatHref(buildChatProjectHref(projectId));
              }}
              onCreateProject={addProject}
              onRenameProject={(projectId, name) => editProject(projectId, { name })}
              onDeleteProject={removeProject}
            />
          </section>
        ) : currentView === "agents" ? (
          <section className="mdc-chat-main" aria-label="Gerenciar agentes">
            {!isDesktop ? (
              <div className="mdc-chat-mobile-nav" role="toolbar" aria-label="Navegação">
                <button type="button" onClick={openMobileSidebar} aria-label="Abrir menu de conversas">
                  Menu
                </button>
              </div>
            ) : null}
            <ChatAgentsPage
              agents={agents}
              selectedAgentKey={activeAgentPageKey}
              canManageAgents={canManageAgents}
              canManageOfficialAgents={canManageOfficialAgents}
              editAgentKey={agentEditRequest?.key ?? null}
              editRequestKey={agentEditRequest?.requestKey ?? 0}
              isLoading={isLoadingAgents}
              onBack={() => {
                clearWorkspaceError();
                setAgentEditRequest(null);
                setCurrentView("chat");
                navigateChatHref(buildChatHref({ kind: "home" }));
              }}
              onSelectAgent={(agentKey) => {
                clearWorkspaceError();
                clearError();
                setCanvasDocument(null);
                setSelectedProjectId(null);
                setActiveAgentPageKey(agentKey);
                setContextAgentKey(null);
                setCurrentView("chat");
                void startSession();
              }}
              onCreateAgent={addAgent}
              onUpdateAgent={editAgent}
              onDeleteAgent={removeAgent}
              onAgentDuplicated={() => {
                void loadAgents(false, true);
              }}
              onReloadAgents={loadAgents}
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
                : conversationAgent
                  ? `${getAgentIcebreakerCount(conversationAgent)} quebra-gelos`
                  : undefined
            }
            onOpenAdmin={openAdmin}
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
            onOpenProjectSettings={() =>
              setProjectSettingsRequestKey((current) => current + 1)
            }
            onDeleteProject={async () => {
              if (!selectedProject) {
                return;
              }

              const confirmed = window.confirm(
                `Excluir o projeto "${selectedProject.name}"?`,
              );

              if (!confirmed) {
                return;
              }

              const deleted = await removeProject(selectedProject.id);

              if (deleted) {
                setSelectedProjectId(null);
                setContextAgentKey(null);
                await handleStartSession();
              }
            }}
            onManageAgents={canManageAgents ? openAgentsDirectory : undefined}
            onClearAgent={() => {
              setActiveAgentPageKey(null);
              setContextAgentKey(null);
              void startSession();
            }}
          />

          {error || workspaceError ? (
            <ChatInlineError
              message={
                error ||
                workspaceError ||
                "Tente novamente em alguns instantes."
              }
              details={error || workspaceError}
              onRetry={() => {
                if (draft.trim()) {
                  void handleSubmitMessage();
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
                <ChatProjectHome
                  project={selectedProject}
                  sessions={selectedProjectSessions}
                  agents={agents}
                  contextAgentKey={contextAgentKey}
                  compact
                  settingsRequestKey={projectSettingsRequestKey}
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
                  onUpdateProject={editProject}
                  getAccessToken={getAccessToken}
                  onUseAgent={handleSelectContextAgent}
                  onOpenAgentPage={(agentKey) => {
                    setCanvasDocument(null);
                    setSelectedProjectId(null);
                    setContextAgentKey(null);
                    setActiveAgentPageKey(agentKey);
                    setCurrentView("chat");
                    void startSession();
                  }}
                  onSetDefaultAgent={async (agentKey) => {
                    const updated = await editProject(selectedProject.id, {
                      defaultAgentKey: agentKey,
                    });

                    if (updated) {
                      setContextAgentKey(agentKey);
                    }

                    return updated;
                  }}
                  onDeleteProject={async (projectId) => {
                    const deleted = await removeProject(projectId);

                    if (deleted) {
                      setSelectedProjectId(null);
                      setContextAgentKey(null);
                      await handleStartSession();
                    }

                    return deleted;
                  }}
                  onClearProject={() => {
                    setSelectedProjectId(null);
                    setContextAgentKey(null);
                    void handleStartSession();
                  }}
                  composer={
                    <ChatInput
                      value={draft}
                      disabled={false}
                      isSending={isComposerBusy}
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
              ) : (
                <>
                  {activeAgentPage ? (
                    <ChatAgentHome
                      agent={activeAgentPage}
                      onUseSuggestion={setDraft}
                      canManageAgent={canManageAgents}
                      onManageAgent={() => {
                        if (!canManageAgents || !activeAgentPage?.key) {
                          return;
                        }

                        setAgentEditRequest({
                          key: activeAgentPage.key,
                          requestKey: Date.now(),
                        });
                        setCurrentView("agents");
                      }}
                    />
                  ) : (
                    <ChatEmptyState
                      displayName={userDisplayName}
                      onUseSuggestion={setDraft}
                    />
                  )}

                  <ChatInput
                    value={draft}
                    disabled={false}
                    isSending={isComposerBusy}
                    variant="center"
                    placeholder={getComposerPlaceholder()}
                    {...composerAttachmentProps}
                    {...(activeAgentPage ? agentPageComposerContextProps : composerContextProps)}
                    onChange={setDraft}
                    onSubmit={handleSubmitMessage}
                    onCancel={cancelStreaming}
                  />
                </>
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
                streamingStatus={streamingStatus}
                isStreaming={isStreamingActiveSession}
                isLoading={isLoadingMessages && messages.length === 0}
                onUseSuggestion={setDraft}
                onEditAndResendMessage={editAndResendMessage}
                onReuseMessage={reuseMessage}
                onMessageFeedback={setMessageFeedback}
              />

              <ChatInput
                value={draft}
                disabled={false}
                isSending={isComposerBusy}
                variant="dock"
                placeholder={getComposerPlaceholder()}
                {...composerAttachmentProps}
                {...composerContextProps}
                onChange={setDraft}
                onSubmit={handleSubmitMessage}
                onCancel={cancelStreaming}
              />
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
      </section>
    </main>
  );
}
