import {
  ArrowDown,
  Check,
  Copy,
  FileText,
  Pencil,
  RotateCcw,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import type {
  ChatMessage,
  ChatSource,
  ChatToolCall,
} from "../../data/api/chatTypes";
import {
  buildChatTimelineItems,
  formatMessageTime,
} from "./chatMessageTimeline";
import { ChatEmptyState } from "./ChatEmptyState";
import { ChatMarkdown } from "./ChatMarkdown";
import { ChatActionResults } from "./ChatActionResults";
import { ChatSources } from "./ChatSources";
import { filterVisibleChatSources } from "./chatSourcesFilter";

import "./ChatMessageList.css";

const SCROLL_NEAR_BOTTOM_THRESHOLD_PX = 96;
const PIN_USER_MESSAGE_TOP_PADDING_PX = 12;

type ChatMessageListProps = {
  messages: ChatMessage[];
  conversationKey?: string | null;
  streamingAnswer?: string;
  streamingSources?: ChatSource[];
  streamingToolCalls?: ChatToolCall[];
  streamingStatus?: string | null;
  isStreaming?: boolean;
  isLoading?: boolean;
  onUseSuggestion?: (value: string) => void;
  onEditMessage?: (messageId: string, content: string) => Promise<ChatMessage | null>;
  onEditAndResendMessage?: (
    messageId: string,
    content: string,
  ) => Promise<ChatMessage | null>;
  onReuseMessage?: (content: string) => void;
  onMessageFeedback?: (messageId: string, rating: -1 | 1 | null) => Promise<void>;
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

function scrollElementToBottom(element: HTMLDivElement, behavior: ScrollBehavior) {
  element.scrollTo({
    top: element.scrollHeight,
    behavior,
  });
}

function isElementNearBottom(element: HTMLDivElement, threshold = SCROLL_NEAR_BOTTOM_THRESHOLD_PX) {
  return (
    element.scrollHeight - element.scrollTop - element.clientHeight <= threshold
  );
}

function getMessageScrollTop(
  list: HTMLDivElement,
  messageId: string,
  padding = PIN_USER_MESSAGE_TOP_PADDING_PX,
): number | null {
  const node = list.querySelector(`[data-message-id="${messageId}"]`);

  if (!(node instanceof HTMLElement)) {
    return null;
  }

  const listTop = list.getBoundingClientRect().top;
  const nodeTop = node.getBoundingClientRect().top;
  const targetTop = nodeTop - listTop + list.scrollTop - padding;

  return Math.max(0, targetTop);
}

function scrollMessageToTopOfList(
  list: HTMLDivElement,
  messageId: string,
  behavior: ScrollBehavior = "auto",
) {
  const targetTop = getMessageScrollTop(list, messageId);

  if (targetTop === null) {
    return;
  }

  list.scrollTo({ top: targetTop, behavior });
}

export function ChatMessageList({
  messages,
  conversationKey,
  streamingAnswer,
  streamingSources,
  streamingToolCalls,
  streamingStatus,
  isStreaming,
  isLoading,
  onUseSuggestion,
  onEditMessage,
  onEditAndResendMessage,
  onReuseMessage,
  onMessageFeedback,
}: ChatMessageListProps) {
  const listRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const previousMessageCountRef = useRef(0);
  const previousConversationKeyRef = useRef<string | null | undefined>(undefined);
  const pendingInitialScrollRef = useRef(false);
  const followStreamRef = useRef(true);
  const wasStreamingRef = useRef(false);
  const pinUserMessageIdRef = useRef<string | null>(null);

  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState("");
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

  const timelineItems = useMemo(() => buildChatTimelineItems(messages), [messages]);

  const updateScrollAffordances = useCallback(() => {
    const list = listRef.current;

    if (!list) {
      return;
    }

    const nearBottom = isElementNearBottom(list);
    followStreamRef.current = nearBottom;
    setShowScrollToBottom(!nearBottom && messages.length > 0);
  }, [messages.length]);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    const list = listRef.current;

    if (!list) {
      return;
    }

    scrollElementToBottom(list, behavior);
    followStreamRef.current = true;
    setShowScrollToBottom(false);
  }, []);

  const alignPinnedUserMessage = useCallback((behavior: ScrollBehavior = "auto") => {
    const list = listRef.current;
    const pinnedId = pinUserMessageIdRef.current;

    if (!list || !pinnedId) {
      return;
    }

    scrollMessageToTopOfList(list, pinnedId, behavior);
    followStreamRef.current = false;
    setShowScrollToBottom(true);
  }, []);

  const isActiveStream = Boolean(isStreaming || streamingAnswer || streamingStatus);

  useEffect(() => {
    if (conversationKey !== previousConversationKeyRef.current) {
      const previousKey = previousConversationKeyRef.current;
      previousConversationKeyRef.current = conversationKey;

      const isSendFlow =
        pinUserMessageIdRef.current !== null || isActiveStream;

      if (isSendFlow && !pinUserMessageIdRef.current) {
        const lastUserMessage = [...messages]
          .reverse()
          .find((message) => message.role === "user");

        if (lastUserMessage?.id) {
          pinUserMessageIdRef.current = lastUserMessage.id;
          followStreamRef.current = false;
        }
      }

      pendingInitialScrollRef.current =
        Boolean(conversationKey) &&
        previousKey !== conversationKey &&
        !isSendFlow;

      if (!pinUserMessageIdRef.current) {
        followStreamRef.current = true;
      }

      setShowScrollToBottom(false);
    }
  }, [conversationKey, isActiveStream, messages]);

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (pendingInitialScrollRef.current && messages.length > 0) {
      pendingInitialScrollRef.current = false;
      requestAnimationFrame(() => {
        scrollToBottom("auto");
      });
      return;
    }

    if (messages.length === 0 && !isActiveStream) {
      previousMessageCountRef.current = 0;
      return;
    }

    const lastMessage = messages[messages.length - 1];
    const userJustSent =
      messages.length > previousMessageCountRef.current &&
      lastMessage?.role === "user";

    previousMessageCountRef.current = messages.length;

    if (userJustSent && lastMessage?.id) {
      pinUserMessageIdRef.current = lastMessage.id;
      followStreamRef.current = false;
      return;
    }

    if (isActiveStream && followStreamRef.current && !pinUserMessageIdRef.current) {
      requestAnimationFrame(() => {
        scrollToBottom("smooth");
      });
    }
  }, [
    isActiveStream,
    isLoading,
    messages,
    scrollToBottom,
  ]);

  useLayoutEffect(() => {
    if (isLoading || !pinUserMessageIdRef.current) {
      return;
    }

    alignPinnedUserMessage("auto");
  }, [
    alignPinnedUserMessage,
    isActiveStream,
    isLoading,
    messages,
    streamingAnswer,
    streamingStatus,
    timelineItems.length,
  ]);

  useEffect(() => {
    const list = listRef.current;

    if (!list) {
      return;
    }

    const handleScroll = () => {
      const pinnedId = pinUserMessageIdRef.current;

      if (pinnedId) {
        const pinnedTop = getMessageScrollTop(list, pinnedId, 0);

        if (
          pinnedTop !== null &&
          list.scrollTop > pinnedTop + PIN_USER_MESSAGE_TOP_PADDING_PX + 48
        ) {
          pinUserMessageIdRef.current = null;
        }
      }

      updateScrollAffordances();
    };

    list.addEventListener("scroll", handleScroll, { passive: true });
    updateScrollAffordances();

    return () => {
      list.removeEventListener("scroll", handleScroll);
    };
  }, [updateScrollAffordances, timelineItems.length, isActiveStream]);

  useEffect(() => {
    const wasStreaming = wasStreamingRef.current;

    if (wasStreaming && !isActiveStream) {
      pinUserMessageIdRef.current = null;

      if (followStreamRef.current) {
        requestAnimationFrame(() => {
          scrollToBottom("auto");
        });
      }
    }

    wasStreamingRef.current = isActiveStream;
  }, [isActiveStream, scrollToBottom]);

  async function handleSaveEdit(messageId: string) {
    const updated = await onEditMessage?.(messageId, editingContent);

    if (updated) {
      setEditingMessageId(null);
      setEditingContent("");
    }
  }

  async function handleSaveAndResend(messageId: string) {
    const updated = await onEditAndResendMessage?.(messageId, editingContent);

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

  function renderMessage(message: ChatMessage) {
    const isUser = message.role === "user";
    const messageTime = formatMessageTime(message.created_at);
    const isPending = Boolean(message.metadata?.optimistic);

    return (
      <article
        key={message.id}
        data-message-id={message.id}
        className={`mdc-chat-message mdc-chat-message--${message.role}${
          isPending ? " mdc-chat-message--pending" : ""
        }`}
      >
        <div className="mdc-chat-message-avatar" aria-hidden="true">
          {isUser ? "V" : "D"}
        </div>

        <div className="mdc-chat-message-card">
          <div className="mdc-chat-message-header">
            {!isUser ? (
              <strong>Minha DELPI Chat</strong>
            ) : (
              <span className="mdc-chat-message-header__spacer" aria-hidden="true" />
            )}

            <div className="mdc-chat-message-meta">
              {messageTime ? (
                <time dateTime={message.created_at}>{messageTime}</time>
              ) : null}

              <div className="mdc-chat-message-actions">
                {isUser ? (
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
                ) : (
                  <>
                    <button
                      className={`mdc-chat-message-action${
                        message.user_feedback === 1 ? " is-active" : ""
                      }`}
                      type="button"
                      aria-label="Resposta útil"
                      title="Resposta útil"
                      onClick={() =>
                        void onMessageFeedback?.(
                          message.id,
                          message.user_feedback === 1 ? null : 1,
                        )
                      }
                    >
                      <ThumbsUp size={15} aria-hidden="true" />
                    </button>

                    <button
                      className={`mdc-chat-message-action${
                        message.user_feedback === -1 ? " is-active" : ""
                      }`}
                      type="button"
                      aria-label="Resposta não útil"
                      title="Resposta não útil"
                      onClick={() =>
                        void onMessageFeedback?.(
                          message.id,
                          message.user_feedback === -1 ? null : -1,
                        )
                      }
                    >
                      <ThumbsDown size={15} aria-hidden="true" />
                    </button>

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
                  </>
                )}
              </div>
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
                <button type="button" onClick={cancelEditMessage}>
                  Cancelar
                </button>
                <button type="button" onClick={() => void handleSaveEdit(message.id)}>
                  Salvar
                </button>
                <button
                  type="button"
                  className="mdc-chat-message-edit-actions__primary"
                  disabled={Boolean(isStreaming)}
                  onClick={() => void handleSaveAndResend(message.id)}
                >
                  Salvar e reenviar
                </button>
              </div>
            </div>
          ) : (
            <>
              <ChatMessageAttachments attachments={getMessageAttachments(message)} />
              <ChatMarkdown content={message.content} compact={isUser} />
            </>
          )}

          {!isUser ? (
            <>
              <ChatActionResults toolCalls={getMessageToolCalls(message)} />
              <ChatSources sources={filterVisibleChatSources(getMessageSources(message))} />
            </>
          ) : null}
        </div>
      </article>
    );
  }

  if (isLoading) {
    return (
      <div className="mdc-chat-message-list-wrap">
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
      </div>
    );
  }

  if (messages.length === 0 && !streamingAnswer && !isStreaming) {
    return <ChatEmptyState onUseSuggestion={onUseSuggestion ?? (() => undefined)} />;
  }

  return (
    <div className="mdc-chat-message-list-wrap">
      <div ref={listRef} className="mdc-chat-message-list" aria-live="polite">
        {timelineItems.map((item) =>
          item.type === "day" ? (
            <div
              key={item.key}
              className="mdc-chat-timeline-day"
              role="separator"
              aria-label={item.label}
            >
              <span>{item.label}</span>
            </div>
          ) : (
            renderMessage(item.message)
          ),
        )}

        {isActiveStream ? (
          <article className="mdc-chat-message mdc-chat-message--assistant mdc-chat-message--streaming">
            <div className="mdc-chat-message-avatar" aria-hidden="true">
              D
            </div>

            <div className="mdc-chat-message-card">
              <div className="mdc-chat-message-header">
                <strong>Minha DELPI Chat</strong>
                <div className="mdc-chat-message-meta">
                  <time dateTime={new Date().toISOString()}>
                    {formatMessageTime(new Date().toISOString())}
                  </time>
                </div>
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

              <ChatActionResults toolCalls={streamingToolCalls} />
              <ChatSources sources={filterVisibleChatSources(streamingSources)} />
            </div>
          </article>
        ) : null}

        <div ref={bottomRef} className="mdc-chat-message-list__anchor" aria-hidden="true" />
      </div>

      {showScrollToBottom ? (
        <button
          type="button"
          className="mdc-chat-scroll-to-bottom"
          aria-label="Ir para as mensagens mais recentes"
          title="Ir para o final"
          onClick={() => scrollToBottom("smooth")}
        >
          <ArrowDown size={18} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
}
