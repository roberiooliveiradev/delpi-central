import { Check, Copy } from "lucide-react";
import { useState } from "react";

import type {
  ChatMessage,
  ChatSource,
  ChatToolCall,
} from "../../data/api/chatTypes";
import { ChatSources } from "./ChatSources";
import { ChatToolCalls } from "./ChatToolCalls";

type ChatMessageListProps = {
  messages: ChatMessage[];
  streamingAnswer?: string;
  streamingSources?: ChatSource[];
  streamingToolCalls?: ChatToolCall[];
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

function getMessageToolCalls(message: ChatMessage): ChatToolCall[] {
  const toolCalls = message.metadata?.toolCalls;

  if (Array.isArray(toolCalls)) {
    return toolCalls;
  }

  return [];
}

async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";

  document.body.appendChild(textarea);
  textarea.select();

  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(textarea);
  }
}

export function ChatMessageList({
  messages,
  streamingAnswer,
  streamingSources,
  streamingToolCalls,
  isLoading,
}: ChatMessageListProps) {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  async function handleCopy(messageId: string, content: string) {
    if (!content.trim()) {
      return;
    }

    await copyTextToClipboard(content);

    setCopiedMessageId(messageId);
    window.setTimeout(() => {
      setCopiedMessageId((current) => (current === messageId ? null : current));
    }, 1800);
  }

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
          <div className="mdc-chat-message-header">
            <strong>
              {message.role === "user" ? "Você" : "Minha DELPI Chat"}
            </strong>

            {message.role === "assistant" ? (
              <button
                className="mdc-chat-message-action"
                type="button"
                onClick={() => void handleCopy(message.id, message.content)}
                aria-label={
                  copiedMessageId === message.id
                    ? "Resposta copiada"
                    : "Copiar resposta"
                }
                title={
                  copiedMessageId === message.id
                    ? "Resposta copiada"
                    : "Copiar resposta"
                }
              >
                {copiedMessageId === message.id ? (
                  <Check size={15} aria-hidden="true" />
                ) : (
                  <Copy size={15} aria-hidden="true" />
                )}
              </button>
            ) : null}
          </div>

          <p>{message.content}</p>

          {message.role === "assistant" ? (
            <>
              <ChatToolCalls toolCalls={getMessageToolCalls(message)} />
              <ChatSources sources={getMessageSources(message)} />
            </>
          ) : null}
        </article>
      ))}

      {streamingAnswer ? (
        <article className="mdc-chat-message mdc-chat-message--assistant mdc-chat-message--streaming">
          <div className="mdc-chat-message-header">
            <strong>Minha DELPI Chat</strong>
          </div>

          <p>{streamingAnswer}</p>
          <ChatToolCalls toolCalls={streamingToolCalls} />
          <ChatSources sources={streamingSources} />
        </article>
      ) : null}
    </div>
  );
}
