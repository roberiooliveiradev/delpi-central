import type { ChatMessage, ChatSource } from "../../data/api/chatTypes";
import { ChatSources } from "./ChatSources";

type ChatMessageListProps = {
  messages: ChatMessage[];
  streamingAnswer?: string;
  streamingSources?: ChatSource[];
  isLoading?: boolean;
};

function getMessageSources(message: ChatMessage): ChatSource[] {
  const directSources = message.metadata?.sources;

  if (Array.isArray(directSources)) {
    return directSources;
  }

  const ragSources = message.metadata?.rag?.sources;

  if (Array.isArray(ragSources)) {
    return ragSources;
  }

  return [];
}

export function ChatMessageList({
  messages,
  streamingAnswer,
  streamingSources,
  isLoading,
}: ChatMessageListProps) {
  if (isLoading) {
    return (
      <div className="mdc-chat-empty">
        <p>Carregando histórico...</p>
      </div>
    );
  }

  if (messages.length === 0 && !streamingAnswer) {
    return (
      <div className="mdc-chat-empty">
        <p>Esta conversa ainda não possui mensagens.</p>
        <small>Digite uma pergunta para iniciar a conversa.</small>
      </div>
    );
  }

  return (
    <div className="mdc-chat-message-list" aria-live="polite">
      {messages.map((message) => (
        <article
          key={message.id}
          className={`mdc-chat-message mdc-chat-message--${message.role}`}
        >
          <strong>{message.role === "user" ? "Você" : "Minha DELPI Chat"}</strong>
          <p>{message.content}</p>

          {message.role === "assistant" ? (
            <ChatSources sources={getMessageSources(message)} />
          ) : null}
        </article>
      ))}

      {streamingAnswer ? (
        <article className="mdc-chat-message mdc-chat-message--assistant mdc-chat-message--streaming">
          <strong>Minha DELPI Chat</strong>
          <p>{streamingAnswer}</p>
          <ChatSources sources={streamingSources} />
        </article>
      ) : null}
    </div>
  );
}
