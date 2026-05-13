import { useEffect, useState } from "react";
import { ChatCanvas, type ChatCanvasDocument } from "../components/ChatCanvas";
import { ChatEmptyState } from "../components/ChatEmptyState";
import "./ChatPage.css";
import { ChatInput } from "../components/ChatInput";
import { ChatMessageList } from "../components/ChatMessageList";
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

type ChatPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onOpenAdmin?: () => void;
};


export function ChatPage({ getAccessToken, onOpenAdmin }: ChatPageProps) {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedAgentKey, setSelectedAgentKey] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<ChatSidebarView>("chat");

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
    addProject,
    editProject,
    removeProject,
    shareProject,
  } = useChatWorkspace({ getAccessToken });

  const [canvasDocument, setCanvasDocument] = useState<ChatCanvasDocument | null>(null);
  const selectedProject = projects.find((project) => project.id === selectedProjectId);
  const selectedAgent = agents.find((agent) => agent.key === selectedAgentKey);
  const selectedProjectName = selectedProject?.name ?? null;
  const selectedAgentName = selectedAgent?.name ?? null;
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

  function handleSelectSession(session: typeof sessions[number]) {
    setCanvasDocument(null);
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
          onNewSession={handleStartSession}
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
          onUpdateProject={editProject}
          onDeleteProject={removeProject}
          onShareProject={shareProject}
          onSelectProject={(projectId) => {
            setSelectedProjectId(projectId);
            void handleStartSession();
          }}
          onSelectAgent={(agentKey) => {
            setSelectedAgentKey(agentKey);
            void handleStartSession();
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
                setSelectedAgentKey(agentKey);
                void handleStartSession();
              }}
                            />
          </section>
        ) : (
        <section className="mdc-chat-main" aria-label="Minha DELPI Chat">
          <header className="mdc-chat-header">
            <div>
              <p className="mdc-chat-eyebrow">Plugin oficial</p>
              <h1>Minha DELPI Chat</h1>
              <p>
                Assistente conversacional corporativo integrado à Minha DELPI.
              </p>

              {selectedProjectName || selectedAgentName ? (
                <div className="mdc-chat-context-chips" aria-label="Contexto selecionado">
                  {selectedProjectName ? <span>Projeto: {selectedProjectName}</span> : null}
                  {selectedAgentName ? <span>Agente: {selectedAgentName}</span> : null}
                </div>
              ) : null}
            </div>

            <div className="mdc-chat-header-actions">
              <button type="button" onClick={onOpenAdmin}>
                Admin
              </button>
              <span className="mdc-chat-status">MVP</span>
            </div>
          </header>

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
                  onSelectSession={handleSelectSession}
                />
              ) : (
                <ChatEmptyState onUseSuggestion={setDraft} />
              )}

              <ChatInput
                value={draft}
                disabled={false}
                isSending={isStreaming}
                variant="center"
                onChange={setDraft}
                onSubmit={sendMessage}
                onCancel={cancelStreaming}
              />
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
