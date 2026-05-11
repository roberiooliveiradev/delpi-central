import { ChatInput } from "../components/ChatInput";
import { ChatMessageList } from "../components/ChatMessageList";
import { ChatSidebar } from "../components/ChatSidebar";
import { useChatSession } from "../../state/hooks/useChatSession";

type ChatPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function ChatPage({ getAccessToken }: ChatPageProps) {
  const {
    sessions,
    activeSession,
    messages,
    draft,
    streamingAnswer,
    isLoadingSessions,
    isLoadingMessages,
    isStreaming,
    error,
    setDraft,
    sendMessage,
    cancelStreaming,
    startSession,
    selectSession,
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

            <span className="mdc-chat-status">MVP</span>
          </header>

          {error ? (
            <div className="mdc-chat-alert" role="alert">
              {error}
            </div>
          ) : null}

          <ChatMessageList
            messages={messages}
            streamingAnswer={streamingAnswer}
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
