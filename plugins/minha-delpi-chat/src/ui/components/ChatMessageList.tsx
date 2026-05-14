import { Check, Copy, FileText, Pencil, RotateCcw } from "lucide-react";
import { useState } from "react";

import type {
  ChatMessage,
  ChatSource,
  ChatToolCall,
} from "../../data/api/chatTypes";
import { ChatEmptyState } from "./ChatEmptyState";
import { ChatMarkdown } from "./ChatMarkdown";
import { ChatSources } from "./ChatSources";
import { ChatToolCalls } from "./ChatToolCalls";

import "./ChatMessageList.css";

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

type MessageAttachment = {
  id?: string;
  filename?: string;
  original_filename?: string;
  content_type?: string | null;
  size_bytes?: number;
  status?: string;
};

function getMessageAttachments(message: ChatMessage): MessageAttachment[] {
  const attachments = message.metadata?.attachments;

  if (!Array.isArray(attachments)) {
    return [];
  }

  return attachments.filter((attachment): attachment is MessageAttachment => {
    return Boolean(attachment && typeof attachment === "object");
  });
}

function formatAttachmentSize(size?: number): string {
  if (!size || size < 0) {
    return "";
  }

  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function ChatMessageAttachments({ attachments }: { attachments: MessageAttachment[] }) {
  if (attachments.length === 0) {
    return null;
  }

  return (
    <div className="mdc-chat-message-attachments" aria-label="Arquivos anexados">
      {attachments.map((attachment, index) => {
        const filename =
          attachment.original_filename ||
          attachment.filename ||
          `Arquivo ${index + 1}`;
        const size = formatAttachmentSize(attachment.size_bytes);

        return (
          <span
            key={attachment.id || `${filename}-${index}`}
            className="mdc-chat-message-attachment"
            title={filename}
          >
            <FileText size={14} aria-hidden="true" />
            <strong>{filename}</strong>
            {size ? <small>{size}</small> : null}
          </span>
        );
      })}
    </div>
  );
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
      <div className="mdc-chat-message-list" aria-live="polite">
        <article className="mdc-chat-message mdc-chat-message--assistant">
          <div className="mdc-chat-message-avatar">D</div>

          <div className="mdc-chat-message-card">
            <div className="mdc-chat-message-header">
              <strong>Minha DELPI Chat</strong>
            </div>

            <div className="mdc-chat-history-loading">
              <span />
              <span />
              <span />
              <p>Carregando histórico da conversa...</p>
            </div>
          </div>
        </article>
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
          <div className="mdc-chat-message-avatar">
            {message.role === "user" ? "V" : "D"}
          </div>

          <div className="mdc-chat-message-card">
            <div className="mdc-chat-message-header">
              <strong>
                {message.role === "user" ? "Você" : "Minha DELPI Chat"}
              </strong>

              <div className="mdc-chat-message-actions">
                {message.role === "user" ? (
                  <>
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
                  </>
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
              <>
                <ChatMessageAttachments attachments={getMessageAttachments(message)} />
                <ChatMarkdown
                  content={message.content}
                  compact={message.role === "user"}
                />
              </>
            )}

            {message.role === "assistant" ? (
              <>
                <ChatToolCalls toolCalls={getMessageToolCalls(message)} />
                <ChatSources sources={getMessageSources(message)} />
              </>
            ) : null}
          </div>
        </article>
      ))}

      {isStreaming || streamingAnswer ? (
        <article className="mdc-chat-message mdc-chat-message--assistant mdc-chat-message--streaming">
          <div className="mdc-chat-message-avatar">D</div>

          <div className="mdc-chat-message-card">
            <div className="mdc-chat-message-header">
              <strong>Minha DELPI Chat</strong>
            </div>

            {streamingAnswer ? (
              <ChatMarkdown content={streamingAnswer} />
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
          </div>
        </article>
      ) : null}
    </div>
  );
}
