import { useEffect, useState } from "react";
import { ChatCanvas, type ChatCanvasDocument } from "../components/ChatCanvas";
import { ChatAgentHome } from "../components/ChatAgentHome";
import { ChatEmptyState } from "../components/ChatEmptyState";
import "./ChatPage.css";
import { ChatInput, type ChatInputAttachment } from "../components/ChatInput";
import { ChatInlineError } from "../components/ChatInlineError";
import { ChatMessageList } from "../components/ChatMessageList";
import { ChatContextTopbar } from "../components/ChatContextTopbar";
import { ChatProjectHome } from "../components/ChatProjectHome";
import { ChatSidebar, type ChatSidebarView } from "../components/ChatSidebar";
import { ChatAgentsPage } from "./ChatAgentsPage";
import {
  createChatArtifact,
  createProjectTextSource,
  deleteChatSource,
  listProjectSources,
  updateChatArtifact,
  uploadProjectSource,
} from "../../data/api/chatApi";
import { useChatSession } from "../../state/hooks/useChatSession";
import { useChatWorkspace } from "../../state/hooks/useChatWorkspace";
import { getDisplayNameFromAccessToken } from "../../utils/authDisplayName";
import { userCanManageChatTools } from "../../security/permissions";

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
  onOpenAdmin?: () => void;
};


export function ChatPage({ getAccessToken, onOpenAdmin }: ChatPageProps) {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [activeAgentPageKey, setActiveAgentPageKey] = useState<string | null>(null);
  const [agentEditRequest, setAgentEditRequest] = useState<{
    key: string;
    requestKey: number;
  } | null>(null);
  const [canManageAgents, setCanManageAgents] = useState(false);

  const [contextAgentKey, setContextAgentKey] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<ChatSidebarView>("chat");
  const [projectSettingsRequestKey, setProjectSettingsRequestKey] = useState(0);
  const [userDisplayName, setUserDisplayName] = useState<string | null>(null);
  const [composerAttachments, setComposerAttachments] = useState<ChatInputAttachment[]>([]);
  const [projectSources, setProjectSources] = useState<Record<string, import("../../data/api/chatTypes").ChatWorkspaceSource[]>>({});
  const [isLoadingProjectSources, setIsLoadingProjectSources] = useState(false);

  const effectiveAgentKey = contextAgentKey ?? activeAgentPageKey;

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
    isStreaming,
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
    editMessage,
    reuseMessage,
  } = useChatSession({
    getAccessToken,
    projectId: selectedProjectId,
    agentKey: effectiveAgentKey,
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
  } = useChatWorkspace({ getAccessToken });

  const [canvasDocument, setCanvasDocument] = useState<ChatCanvasDocument | null>(null);
  const selectedProject = projects.find((project) => project.id === selectedProjectId);
  const activeAgentPage = agents.find((agent) => agent.key === activeAgentPageKey);
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

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    return localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY) === "true";
  });

  useEffect(() => {
    localStorage.setItem(
      SIDEBAR_COLLAPSED_STORAGE_KEY,
      String(isSidebarCollapsed),
    );
  }, [isSidebarCollapsed]);

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
      const allowed = await userCanManageChatTools(async () => {
        const token = await getAccessToken?.();

        return token ?? null;
      });

      if (isMounted) {
        setCanManageAgents(allowed);
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
    clearWorkspaceError();
    clearError();
    setCanvasDocument(null);
    setSelectedProjectId(null);
    setActiveAgentPageKey(null);
    setContextAgentKey(null);
    setCurrentView("chat");
    await startSession();
  }

  function handleSelectSession(session: typeof sessions[number]) {
    clearWorkspaceError();
    clearError();
    setCanvasDocument(null);
    setComposerAttachments([]);
    setSelectedProjectId(session.project_id ?? null);
    setActiveAgentPageKey(null);
    setContextAgentKey(session.agent_key ?? null);
    setCurrentView("chat");
    selectSession(session);
  }

  async function handleDeleteSession(sessionId: string) {
    setCanvasDocument(null);
    return deleteSession(sessionId);
  }

  function handleAttachFiles(files: File[]) {
    const nextAttachments = files.map((file) => ({
      id: `${file.name}-${file.size}-${file.lastModified}-${crypto.randomUUID()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      file,
    }));

    setComposerAttachments((current) => [...current, ...nextAttachments].slice(0, 10));
  }

  function handleRemoveAttachment(attachmentId: string) {
    setComposerAttachments((current) =>
      current.filter((attachment) => attachment.id !== attachmentId),
    );
  }

  async function handleSubmitMessage() {
    const files = composerAttachments.map((attachment) => attachment.file);

    await sendMessage({ attachments: files });

    if (draft.trim()) {
      setComposerAttachments([]);
    }
  }

  const isConversationEmpty =
    !isLoadingMessages &&
    messages.length === 0 &&
    !streamingAnswer &&
    !isStreaming;

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

    if (activeAgentPage) {
      return `Pergunte ao agente ${activeAgentPage.name}`;
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

  return (
    <main className="minha-delpi-chat">
      <section
        className={
          isSidebarCollapsed
            ? "mdc-chat-shell mdc-chat-shell--sidebar-collapsed"
            : "mdc-chat-shell"
        }
      >
        <ChatSidebar
          sessions={sessions}
          archivedSessions={archivedSessions}
          agents={agents}
          projects={projects}
          activeSessionId={activeSession?.id}
          selectedProjectId={selectedProjectId}
          selectedAgentKey={activeAgentPageKey}
          isLoading={isLoadingSessions}
          isLoadingArchivedSessions={isLoadingArchivedSessions}
          isLoadingAgents={isLoadingAgents}
          isLoadingProjects={isLoadingProjects}
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
            clearWorkspaceError();
            clearError();
            setCanvasDocument(null);
            setSelectedProjectId(projectId);
            setActiveAgentPageKey(null);
            setContextAgentKey(getProjectDefaultAgentKey(projectId));
            setCurrentView("chat");
            void startSession();
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
          isCollapsed={isSidebarCollapsed}
          onToggleCollapsed={() => setIsSidebarCollapsed((current) => !current)}
          onViewChange={setCurrentView}
        />

        {currentView === "agents" ? (
          <section className="mdc-chat-main" aria-label="Gerenciar agentes">
            <ChatAgentsPage
              agents={agents}
              selectedAgentKey={activeAgentPageKey}
              canManageAgents={canManageAgents}
              editAgentKey={agentEditRequest?.key ?? null}
              editRequestKey={agentEditRequest?.requestKey ?? 0}
              isLoading={isLoadingAgents}
              onBack={() => {
                clearWorkspaceError();
                setAgentEditRequest(null);
                setCurrentView("chat");
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
              getAccessToken={getAccessToken}
            />
          </section>
        ) : (
        <section className="mdc-chat-main" aria-label="Minha DELPI Chat">
          <ChatContextTopbar
            mode={selectedProject ? "project" : activeAgentPage ? "agent" : "general"}
            title={
              selectedProject?.name ||
              activeAgentPage?.name ||
              "Minha DELPI Chat"
            }
            subtitle={
              selectedProject
                ? contextAgent
                  ? `Projeto usando ${contextAgent.name}`
                  : "Projeto selecionado"
                : activeAgentPage
                  ? "Página do agente"
                  : contextAgent
                    ? `Chat usando ${contextAgent.name}`
                    : "Assistente corporativo"
            }
            badge={
              selectedProject
                ? `${selectedProjectSessions.length} chats`
                : activeAgentPage
                  ? `${getAgentIcebreakerCount(activeAgentPage)} quebra-gelos`
                  : undefined
            }
            onOpenAdmin={onOpenAdmin}
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
            onManageAgents={() => {
              clearWorkspaceError();
              setCurrentView("agents");
            }}
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
                      isSending={isStreaming}
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
                      onManageAgent={() => {
                        if (!activeAgentPage?.key) {
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
                    isSending={isStreaming}
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
            <>
              <ChatMessageList
                messages={messages}
                streamingAnswer={streamingAnswer}
                streamingSources={streamingSources}
                streamingToolCalls={streamingToolCalls}
                streamingStatus={streamingStatus}
                isStreaming={isStreaming}
                isLoading={isLoadingMessages}
                onUseSuggestion={setDraft}
                onEditMessage={editMessage}
                onReuseMessage={reuseMessage}
              />

              <ChatInput
                value={draft}
                disabled={false}
                isSending={isStreaming}
                placeholder={getComposerPlaceholder()}
                {...composerAttachmentProps}
                {...composerContextProps}
                onChange={setDraft}
                onSubmit={handleSubmitMessage}
                onCancel={cancelStreaming}
              />
            </>
          )}
        </section>
        )}

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
