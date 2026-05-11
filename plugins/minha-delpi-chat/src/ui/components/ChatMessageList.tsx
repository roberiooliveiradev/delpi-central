import type { ChatMessage } from "../../data/api/chatTypes";

type ChatMessageListProps = {
  messages: ChatMessage[];
  streamingAnswer?: string;
  isLoading?: boolean;
};

export function ChatMessageList({
  messages,
  streamingAnswer,
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
        </article>
      ))}

      {streamingAnswer ? (
        <article className="mdc-chat-message mdc-chat-message--assistant mdc-chat-message--streaming">
          <strong>Minha DELPI Chat</strong>
          <p>{streamingAnswer}</p>
        </article>
      ) : null}
    </div>
  );
}
