import { useEffect, useState } from "react";
import { ChatCanvas, type ChatCanvasDocument } from "../components/ChatCanvas";
import { ChatAgentHome } from "../components/ChatAgentHome";
import { ChatEmptyState } from "../components/ChatEmptyState";
import "./ChatPage.css";
import { ChatInput } from "../components/ChatInput";
import { ChatMessageList } from "../components/ChatMessageList";
import { ChatContextTopbar } from "../components/ChatContextTopbar";
import { ChatProjectHome } from "../components/ChatProjectHome";
import { ChatSidebar, type ChatSidebarView } from "../components/ChatSidebar";
import { ChatAgentsPage } from "./ChatAgentsPage";
import {
  createChatArtifact,
  updateChatArtifact,
} from "../../data/api/chatApi";
import { useChatSession } from "../../state/hooks/useChatSession";
import { useChatWorkspace } from "../../state/hooks/useChatWorkspace";

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
  const [selectedAgentKey, setSelectedAgentKey] = useState<string | null>(null);
  const [isAgentContextOnly, setIsAgentContextOnly] = useState(false);
  const [currentView, setCurrentView] = useState<ChatSidebarView>("chat");
  const [projectSettingsRequestKey, setProjectSettingsRequestKey] = useState(0);

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
    agentKey: selectedAgentKey,
  });

  const {
    agents,
    projects,
    isLoadingAgents,
    isLoadingProjects,
    workspaceError,
    addAgent,
    editAgent,
    removeAgent,
    addProject,
    editProject,
    removeProject,
  } = useChatWorkspace({ getAccessToken });

  const [canvasDocument, setCanvasDocument] = useState<ChatCanvasDocument | null>(null);
  const selectedProject = projects.find((project) => project.id === selectedProjectId);
  const selectedAgent = agents.find((agent) => agent.key === selectedAgentKey);
  const selectedProjectSessions = selectedProjectId
    ? sessions.filter((session) => session.project_id === selectedProjectId)
    : [];

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    return localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY) === "true";
  });

  useEffect(() => {
    localStorage.setItem(
      SIDEBAR_COLLAPSED_STORAGE_KEY,
      String(isSidebarCollapsed),
    );
  }, [isSidebarCollapsed]);


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
    await startSession();
  }

  async function handleStartGeneralSession() {
    setCanvasDocument(null);
    setSelectedProjectId(null);
    setSelectedAgentKey(null);
    setIsAgentContextOnly(false);
    setCurrentView("chat");
    await startSession();
  }

  function handleSelectSession(session: typeof sessions[number]) {
    setCanvasDocument(null);
    setSelectedProjectId(session.project_id ?? null);
    setSelectedAgentKey(session.agent_key ?? null);
    setIsAgentContextOnly(Boolean(session.agent_key));
    setCurrentView("chat");
    selectSession(session);
  }

  async function handleDeleteSession(sessionId: string) {
    setCanvasDocument(null);
    return deleteSession(sessionId);
  }

  const isConversationEmpty =
    !isLoadingMessages &&
    messages.length === 0 &&
    !streamingAnswer &&
    !isStreaming;

  function getComposerPlaceholder() {
    if (selectedProject && selectedAgent) {
      return `Novo chat em ${selectedProject.name} usando ${selectedAgent.name}`;
    }

    if (selectedProject) {
      return `Novo chat em ${selectedProject.name}`;
    }

    if (selectedAgent) {
      return `Pergunte ao agente ${selectedAgent.name}`;
    }

    return "Pergunte alguma coisa";
  }

  async function handleSelectContextAgent(agentKey: string | null) {
    setSelectedAgentKey(agentKey);
    setIsAgentContextOnly(Boolean(agentKey));
  }

  async function handleSelectContextProject(projectId: string | null) {
    setSelectedProjectId(projectId);
  }

  const composerContextProps = {
    agents,
    projects,
    selectedAgentKey,
    selectedProjectId,
    onSelectAgent: handleSelectContextAgent,
    onSelectProject: handleSelectContextProject,
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
          selectedAgentKey={selectedAgentKey}
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
            setSelectedProjectId(projectId);
            setIsAgentContextOnly(false);
            setCurrentView("chat");
          }}
          onSelectAgent={(agentKey) => {
            setSelectedProjectId(null);
            setSelectedAgentKey(agentKey);
            setIsAgentContextOnly(false);
            setCurrentView("chat");
          }}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapsed={() => setIsSidebarCollapsed((current) => !current)}
          onViewChange={setCurrentView}
        />

        {currentView === "agents" ? (
          <section className="mdc-chat-main" aria-label="Gerenciar agentes">
            <ChatAgentsPage
              agents={agents}
              selectedAgentKey={selectedAgentKey}
              isLoading={isLoadingAgents}
              onBack={() => setCurrentView("chat")}
              onSelectAgent={(agentKey) => {
                setSelectedProjectId(null);
                setSelectedAgentKey(agentKey);
                setIsAgentContextOnly(false);
                setCurrentView("chat");
              }}
              onCreateAgent={addAgent}
              onUpdateAgent={editAgent}
              onDeleteAgent={removeAgent}
            />
          </section>
        ) : (
        <section className="mdc-chat-main" aria-label="Minha DELPI Chat">
          <ChatContextTopbar
            mode={selectedProject ? "project" : selectedAgent ? "agent" : "general"}
            title={
              selectedProject?.name ||
              selectedAgent?.name ||
              "Minha DELPI Chat"
            }
            subtitle={
              selectedProject
                ? "Projeto selecionado"
                : selectedAgent
                  ? "Chat com agente"
                  : "Assistente corporativo"
            }
            badge={
              selectedProject
                ? `${selectedProjectSessions.length} chats`
                : selectedAgent
                  ? `${getAgentIcebreakerCount(selectedAgent)} quebra-gelos`
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
                setIsAgentContextOnly(false);
                await handleStartSession();
              }
            }}
            onManageAgents={() => setCurrentView("agents")}
            onClearAgent={() => {
              setSelectedAgentKey(null);
              setIsAgentContextOnly(false);
            }}
          />

          {error || workspaceError ? (
            <div className="mdc-chat-alert" role="alert">
              {error || workspaceError}
            </div>
          ) : null}

          {isConversationEmpty ? (
            <section className="mdc-chat-empty-composer">
              {selectedProject ? (
                <ChatProjectHome
                  project={selectedProject}
                  sessions={selectedProjectSessions}
                  compact
                  settingsRequestKey={projectSettingsRequestKey}
                  activeSessionId={activeSession?.id}
                  onSelectSession={handleSelectSession}
                  onRenameSession={renameSession}
                  onDeleteSession={handleDeleteSession}
                  onPinSession={pinSession}
                  onUnpinSession={unpinSession}
                  onUpdateProject={editProject}
                  onDeleteProject={async (projectId) => {
                    const deleted = await removeProject(projectId);

                    if (deleted) {
                      setSelectedProjectId(null);
                      await handleStartSession();
                    }

                    return deleted;
                  }}
                  onClearProject={() => {
                    setSelectedProjectId(null);
                    void handleStartSession();
                  }}
                  composer={
                    <ChatInput
                      value={draft}
                      disabled={false}
                      isSending={isStreaming}
                      variant="center"
                      placeholder={getComposerPlaceholder()}
                      {...composerContextProps}
                      onChange={setDraft}
                      onSubmit={sendMessage}
                      onCancel={cancelStreaming}
                    />
                  }
                />
              ) : (
                <>
                  {selectedAgent && !isAgentContextOnly ? (
                    <ChatAgentHome
                      agent={selectedAgent}
                      onUseSuggestion={setDraft}
                    />
                  ) : (
                    <ChatEmptyState
                      activeAgentName={
                        selectedAgent && isAgentContextOnly ? selectedAgent.name : null
                      }
                      onUseSuggestion={setDraft}
                    />
                  )}

                  <ChatInput
                    value={draft}
                    disabled={false}
                    isSending={isStreaming}
                    variant="center"
                    placeholder={getComposerPlaceholder()}
                    {...composerContextProps}
                    onChange={setDraft}
                    onSubmit={sendMessage}
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
                {...composerContextProps}
                onChange={setDraft}
                onSubmit={sendMessage}
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
