import { ChatInput } from "../components/ChatInput";
import { ChatMessageList } from "../components/ChatMessageList";
import { ChatSidebar } from "../components/ChatSidebar";
import { useChatSession } from "../../state/hooks/useChatSession";

type ChatPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onOpenAdmin?: () => void;
};

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
    renameSession,
  } = useChatSession({ getAccessToken });

  return (
    <main className="minha-delpi-chat">
      <section className="mdc-chat-shell">
        <ChatSidebar
          sessions={sessions}
          activeSessionId={activeSession?.id}
          isLoading={isLoadingSessions}
          onNewSession={startSession}
          onSelectSession={selectSession}
          onRenameSession={renameSession}
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

          <ChatMessageList
            messages={messages}
            streamingAnswer={streamingAnswer}
            streamingSources={streamingSources}
            streamingToolCalls={streamingToolCalls}
            streamingStatus={streamingStatus}
            isStreaming={isStreaming}
            isLoading={isLoadingMessages}
          />

          <ChatInput
            value={draft}
            disabled={!activeSession}
            isSending={isStreaming}
            onChange={setDraft}
            onSubmit={sendMessage}
            onCancel={cancelStreaming}
          />
        </section>
      </section>
    </main>
  );
}
