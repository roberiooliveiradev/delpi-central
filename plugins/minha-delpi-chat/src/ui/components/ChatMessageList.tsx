import { Check, Copy, Pencil, RotateCcw } from "lucide-react";
import "./ChatMessageList.css";
import { useState } from "react";

import type {
  ChatMessage,
  ChatSource,
  ChatToolCall,
} from "../../data/api/chatTypes";
import { ChatSources } from "./ChatSources";
import { ChatEmptyState } from "./ChatEmptyState";
import { ChatToolCalls } from "./ChatToolCalls";

type ChatMessageListProps = {
  messages: ChatMessage[];
  streamingAnswer?: string;
  streamingSources?: ChatSource[];
  streamingToolCalls?: ChatToolCall[];
  streamingStatus?: string | null;
  isStreaming?: boolean;
  isLoading?: boolean;
  onUseSuggestion?: (value: string) => void;
  onEditMessage?: (messageId: string, content: string) => Promise<ChatMessage | null>;
  onReuseMessage?: (content: string) => void;
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
  streamingStatus,
  isStreaming,
  isLoading,
  onUseSuggestion,
  onEditMessage,
  onReuseMessage,
}: ChatMessageListProps) {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState("");

  async function handleSaveEdit(messageId: string) {
    const updated = await onEditMessage?.(messageId, editingContent);

    if (updated) {
      setEditingMessageId(null);
      setEditingContent("");
    }
  }

  function startEditMessage(message: ChatMessage) {
    setEditingMessageId(message.id);
    setEditingContent(message.content);
  }

  function cancelEditMessage() {
    setEditingMessageId(null);
    setEditingContent("");
  }

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

  if (messages.length === 0 && !streamingAnswer && !isStreaming) {
    return <ChatEmptyState onUseSuggestion={onUseSuggestion ?? (() => undefined)} />;
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

            {message.role === "user" ? (
              <div className="mdc-chat-message-user-actions">
                <button
                  className="mdc-chat-message-action"
                  type="button"
                  onClick={() => startEditMessage(message)}
                  aria-label="Editar mensagem"
                  title="Editar mensagem"
                >
                  <Pencil size={15} aria-hidden="true" />
                </button>

                <button
                  className="mdc-chat-message-action"
                  type="button"
                  onClick={() => onReuseMessage?.(message.content)}
                  aria-label="Reutilizar mensagem"
                  title="Reutilizar mensagem"
                >
                  <RotateCcw size={15} aria-hidden="true" />
                </button>
              </div>
            ) : null}

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

          {editingMessageId === message.id ? (
            <div className="mdc-chat-message-edit">
              <textarea
                value={editingContent}
                autoFocus
                onChange={(event) => setEditingContent(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Escape") {
                    event.preventDefault();
                    cancelEditMessage();
                  }

                  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                    event.preventDefault();
                    void handleSaveEdit(message.id);
                  }
                }}
              />

              <div className="mdc-chat-message-edit-actions">
                <button type="button" onClick={() => void handleSaveEdit(message.id)}>
                  Salvar
                </button>
                <button type="button" onClick={cancelEditMessage}>
                  Cancelar
                </button>
              </div>
            </div>
          ) : (
            <p>{message.content}</p>
          )}

          {message.role === "assistant" ? (
            <>
              <ChatToolCalls toolCalls={getMessageToolCalls(message)} />
              <ChatSources sources={getMessageSources(message)} />
            </>
          ) : null}
        </article>
      ))}

      {isStreaming || streamingAnswer ? (
        <article className="mdc-chat-message mdc-chat-message--assistant mdc-chat-message--streaming">
          <div className="mdc-chat-message-header">
            <strong>Minha DELPI Chat</strong>
          </div>

          {streamingAnswer ? (
            <p>{streamingAnswer}</p>
          ) : (
            <div className="mdc-chat-thinking" role="status" aria-live="polite">
              <span className="mdc-chat-thinking__dot" />
              <span className="mdc-chat-thinking__dot" />
              <span className="mdc-chat-thinking__dot" />
              <p>{streamingStatus || "Processando sua solicitação..."}</p>
            </div>
          )}

          <ChatToolCalls toolCalls={streamingToolCalls} />
          <ChatSources sources={streamingSources} />
        </article>
      ) : null}
    </div>
  );
}
