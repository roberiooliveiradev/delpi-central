import { useEffect, useState } from "react";
import { ChatCanvas, type ChatCanvasDocument } from "../components/ChatCanvas";
import { ChatEmptyState } from "../components/ChatEmptyState";
import "./ChatPage.css";
import { ChatInput } from "../components/ChatInput";
import { ChatMessageList } from "../components/ChatMessageList";
import { ChatSidebar } from "../components/ChatSidebar";
import { useChatSession } from "../../state/hooks/useChatSession";

const SIDEBAR_COLLAPSED_STORAGE_KEY = "minha-delpi-chat.sidebar-collapsed";

type ChatPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onOpenAdmin?: () => void;
};

function normalizeCanvasMarkdown(content: string): string {
  return content
    .replace(/\n\s*[-•]\s+/g, "\n- ")
    .replace(/:\n\s*- /g, ":\n\n- ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function ChatPage({ getAccessToken, onOpenAdmin }: ChatPageProps) {
  const {
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
  } = useChatSession({ getAccessToken });

  const [canvasDocument, setCanvasDocument] = useState<ChatCanvasDocument | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    return localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY) === "true";
  });

  useEffect(() => {
    localStorage.setItem(
      SIDEBAR_COLLAPSED_STORAGE_KEY,
      String(isSidebarCollapsed),
    );
  }, [isSidebarCollapsed]);

  function openCanvasFromMessage(content: string, title = "Rascunho da resposta") {
    setCanvasDocument({
      title,
      markdown: normalizeCanvasMarkdown(content),
    });
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
          activeSessionId={activeSession?.id}
          isLoading={isLoadingSessions}
          onNewSession={handleStartSession}
          onSelectSession={handleSelectSession}
          onRenameSession={renameSession}
          onDeleteSession={handleDeleteSession}
          onPinSession={pinSession}
          onUnpinSession={unpinSession}
          onArchiveSession={archiveSession}
          onUnarchiveSession={unarchiveSession}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapsed={() => setIsSidebarCollapsed((current) => !current)}
        />

        <section className="mdc-chat-main" aria-label="Minha DELPI Chat">
          <header className="mdc-chat-header">
            <div>
              <p className="mdc-chat-eyebrow">Plugin oficial</p>
              <h1>Minha DELPI Chat</h1>
              <p>
                Assistente conversacional corporativo integrado à Minha DELPI.
              </p>
            </div>

            <div className="mdc-chat-header-actions">
              <button type="button" onClick={onOpenAdmin}>
                Admin
              </button>
              <span className="mdc-chat-status">MVP</span>
            </div>
          </header>

          {error ? (
            <div className="mdc-chat-alert" role="alert">
              {error}
            </div>
          ) : null}

          {isConversationEmpty ? (
            <section className="mdc-chat-empty-composer">
              <ChatEmptyState onUseSuggestion={setDraft} />

              <ChatInput
                value={draft}
                disabled={!activeSession}
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
                onOpenCanvas={openCanvasFromMessage}
              />

              <ChatInput
                value={draft}
                disabled={!activeSession}
                isSending={isStreaming}
                onChange={setDraft}
                onSubmit={sendMessage}
                onCancel={cancelStreaming}
              />
            </>
          )}
        </section>

        <ChatCanvas
          document={canvasDocument}
          onChange={setCanvasDocument}
          onClose={() => setCanvasDocument(null)}
        />
      </section>
    </main>
  );
}
