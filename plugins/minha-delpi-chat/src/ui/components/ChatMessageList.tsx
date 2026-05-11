import type { ChatMessage } from "../../data/api/chatTypes";

type ChatMessageListProps = {
  messages: ChatMessage[];
  isLoading?: boolean;
};

export function ChatMessageList({ messages, isLoading }: ChatMessageListProps) {
  if (isLoading) {
    return (
      <div className="mdc-chat-empty">
        <p>Carregando histórico...</p>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="mdc-chat-empty">
        <p>Esta conversa ainda não possui mensagens.</p>
        <small>O envio ao LLM será implementado na próxima etapa do roadmap.</small>
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
    </div>
  );
}
