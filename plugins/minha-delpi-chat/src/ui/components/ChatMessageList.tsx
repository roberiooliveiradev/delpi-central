import {
  ArrowDown,
  Check,
  Copy,
  Download,
  FileText,
  GitBranch,
  Pencil,
  RotateCcw,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { useStreamingTextReveal } from "../../state/hooks/useStreamingTextReveal";

import type {
  ChatCanvasOpenPayload,
  ChatMessage,
  ChatSource,
  ChatStreamActivityEntry,
  ChatToolCall,
  ChatWebSearchResearch,
} from "../../data/api/chatTypes";
import {
  buildChatTimelineItems,
  formatMessageTime,
} from "./chatMessageTimeline";
import { ChatBranchNavigator } from "./ChatBranchNavigator";
import { ChatEmptyState } from "./ChatEmptyState";
import { ChatFollowUpChips, type ChatFollowUpSuggestion } from "./ChatFollowUpChips";
import { ChatMessageFeedbackPanel } from "./ChatMessageFeedbackPanel";
import { ChatMarkdown } from "./ChatMarkdown";
import { ChatActionResults } from "./ChatActionResults";
import { ChatAdminDebugPanel } from "./ChatAdminDebugPanel";
import { isAssistantGenerating } from "../../state/chatMessageDelivery";
import { ChatRichPresentation } from "./ChatRichPresentation";
import {
  buildAssistantCopyText,
  getPresentationPairFromToolCalls,
  isShortPresentationCaption,
  shouldShowRichPresentation,
  shouldShowActionResults,
  shouldSuppressMarkdownForPresentation,
} from "./chatPresentation";
import { ChatSources } from "./ChatSources";
import { ChatTrustBadges, type ChatTrustSignal } from "./ChatTrustBadges";
import {
  ChatActionConfirmationPanel,
  type ChatActionConfirmation,
} from "./ChatActionConfirmationPanel";
import { ChatStreamingActivityPanel } from "./ChatStreamingActivityPanel";
import { ChatInlineCanvas } from "./ChatInlineCanvas";
import { ChatMessageEditField } from "./ChatMessageEditField";
import { getCanvasOpenFromMetadata } from "./chatCanvas";
import { filterVisibleChatSources } from "./chatSourcesFilter";

import "./ChatMessageList.css";
import "./ChatRichTable.css";
import "./ChatRichChart.css";

const SCROLL_NEAR_BOTTOM_THRESHOLD_PX = 96;
const PIN_USER_MESSAGE_TOP_PADDING_PX = 12;
const NEAR_RESPONSE_VIEWPORT_SLACK_PX = 120;

type ChatMessageListProps = {
  messages: ChatMessage[];
  conversationKey?: string | null;
  streamingAnswer?: string;
  streamingSources?: ChatSource[];
  streamingToolCalls?: ChatToolCall[];
  streamingAdminDebug?: Record<string, unknown> | null;
  streamingStatus?: string | null;
  streamingActivityLog?: ChatStreamActivityEntry[];
  streamingShowPresentation?: boolean;
  streamingCanvasOpen?: ChatCanvasOpenPayload | null;
  isStreaming?: boolean;
  isPlaybackActive?: boolean;
  isLoading?: boolean;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
  onEditAndResendMessage?: (
    messageId: string,
    content: string,
  ) => Promise<ChatMessage | null>;
  onReuseMessage?: (content: string) => void;
  onDrillDown?: (query: string) => void;
  onMessageFeedback?: (
    messageId: string,
    rating: -1 | 1 | null,
    reason?: string | null,
  ) => Promise<{ thanksMessage?: string } | void>;
  onDownloadAttachment?: (attachmentId: string) => Promise<void>;
  onSwitchMessageBranch?: (
    anchorUserMessageId: string,
    sourceUserMessageId: string,
  ) => Promise<void>;
  branchSwitchingMessageId?: string | null;
  onContinueFromMessage?: (messageId: string) => Promise<void>;
  lastSentUserText?: string;
};

function resolveUserMessageContent(
  message: ChatMessage,
  lastSentUserText: string | undefined,
  isLatestUserMessage: boolean,
): string {
  const content = String(message.content ?? "").trim();

  if (content) {
    return content;
  }

  if (
    message.role === "user" &&
    isLatestUserMessage &&
    lastSentUserText?.trim()
  ) {
    return lastSentUserText.trim();
  }

  return "";
}

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

function getWebSearchResearch(message: ChatMessage): ChatWebSearchResearch | null {
  const research = message.metadata?.webSearchResearch;

  if (!research || typeof research !== "object") {
    return null;
  }

  return research;
}

function getMessageToolCalls(message: ChatMessage): ChatToolCall[] {
  const toolCalls = message.metadata?.toolCalls;

  if (Array.isArray(toolCalls)) {
    return toolCalls;
  }

  return [];
}

function renderPresentation(
  toolCalls: ChatToolCall[],
  textContent: string | null | undefined,
  onDrillDown?: (query: string) => void,
) {
  if (!toolCalls || !toolCalls.length) {
    return null;
  }

  return (
    <ChatRichPresentation
      toolCalls={toolCalls}
      textContent={textContent}
      onDrillDown={onDrillDown}
    />
  );
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

function ChatMessageAttachments({
  attachments,
  onDownloadAttachment,
}: {
  attachments: MessageAttachment[];
  onDownloadAttachment?: (attachmentId: string) => Promise<void>;
}) {
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
        const canDownload = Boolean(attachment.id && onDownloadAttachment);

        return (
          <span
            key={attachment.id || `${filename}-${index}`}
            className="mdc-chat-message-attachment"
            title={filename}
          >
            <FileText size={14} aria-hidden="true" />
            <strong>{filename}</strong>
            {size ? <small>{size}</small> : null}
            {canDownload ? (
              <button
                type="button"
                className="mdc-chat-message-attachment__download"
                onClick={() => void onDownloadAttachment?.(attachment.id!)}
                aria-label={`Baixar ${filename}`}
                title="Baixar arquivo"
              >
                <Download size={14} aria-hidden="true" />
              </button>
            ) : null}
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
  const node = list.querySelector(`[data-message-id="${messageId}"]`);

  if (node instanceof HTMLElement) {
    node.scrollIntoView({ behavior, block: "start" });
    return;
  }

  const targetTop = getMessageScrollTop(list, messageId);

  if (targetTop === null) {
    return;
  }

  list.scrollTo({ top: targetTop, behavior });
}

function scrollElementToAlignTop(
  list: HTMLDivElement,
  node: HTMLElement,
  padding = PIN_USER_MESSAGE_TOP_PADDING_PX,
  behavior: ScrollBehavior = "auto",
) {
  const listTop = list.getBoundingClientRect().top;
  const nodeTop = node.getBoundingClientRect().top;
  const targetTop = nodeTop - listTop + list.scrollTop - padding;

  list.scrollTo({ top: Math.max(0, targetTop), behavior });
}

function isViewportNearResponse(
  list: HTMLDivElement,
  pinnedId: string | null,
): boolean {
  if (isElementNearBottom(list)) {
    return true;
  }

  const streaming = list.querySelector(".mdc-chat-message--streaming");

  if (streaming instanceof HTMLElement) {
    const listRect = list.getBoundingClientRect();
    const nodeRect = streaming.getBoundingClientRect();
    const visibleTop = Math.max(listRect.top, nodeRect.top);
    const visibleBottom = Math.min(listRect.bottom, nodeRect.bottom);

    if (visibleBottom - visibleTop > 24) {
      return true;
    }

    const distanceBelow = nodeRect.top - listRect.bottom;
    const distanceAbove = listRect.top - nodeRect.bottom;

    if (
      distanceBelow > -NEAR_RESPONSE_VIEWPORT_SLACK_PX &&
      distanceAbove < list.clientHeight
    ) {
      return true;
    }
  }

  if (!pinnedId) {
    return false;
  }

  const pinnedTop = getMessageScrollTop(list, pinnedId, 0);

  if (pinnedTop === null) {
    return false;
  }

  const viewTop = list.scrollTop;
  const viewBottom = viewTop + list.clientHeight;

  return (
    viewBottom >= pinnedTop - NEAR_RESPONSE_VIEWPORT_SLACK_PX &&
    viewTop <= list.scrollHeight + NEAR_RESPONSE_VIEWPORT_SLACK_PX
  );
}

function scrollResponseStartIntoView(list: HTMLDivElement): boolean {
  const streaming = list.querySelector(".mdc-chat-message--streaming");

  if (streaming instanceof HTMLElement) {
    scrollElementToAlignTop(list, streaming, 12);
    return true;
  }

  const assistants = list.querySelectorAll(".mdc-chat-message--assistant");
  const lastAssistant = assistants[assistants.length - 1];

  if (lastAssistant instanceof HTMLElement) {
    scrollElementToAlignTop(list, lastAssistant, 12);
    return true;
  }

  return false;
}

export function ChatMessageList({
  messages,
  conversationKey,
  streamingAnswer,
  streamingSources,
  streamingToolCalls,
  streamingAdminDebug,
  streamingStatus,
  streamingActivityLog = [],
  streamingShowPresentation = true,
  streamingCanvasOpen = null,
  isStreaming,
  isPlaybackActive = false,
  isLoading,
  onEditAndResendMessage,
  onReuseMessage,
  onDrillDown,
  onMessageFeedback,
  onDownloadAttachment,
  onSwitchMessageBranch,
  branchSwitchingMessageId = null,
  onContinueFromMessage,
  onOpenCanvas,
  lastSentUserText = "",
}: ChatMessageListProps) {
  const [feedbackThanksByMessageId, setFeedbackThanksByMessageId] = useState<
    Record<string, string>
  >({});
  const [feedbackReasonPickerFor, setFeedbackReasonPickerFor] = useState<string | null>(
    null,
  );
  const listRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const previousMessageCountRef = useRef(0);
  const previousConversationKeyRef = useRef<string | null | undefined>(undefined);
  const pendingInitialScrollRef = useRef(false);
  const followStreamRef = useRef(true);
  const wasStreamingRef = useRef(false);
  const pinUserMessageIdRef = useRef<string | null>(null);
  const pinAlignmentAppliedForRef = useRef<string | null>(null);
  const userScrollIntentRef = useRef(false);
  const pendingScrollToResponseRef = useRef(false);

  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState("");
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);
  const [enteringAssistantId, setEnteringAssistantId] = useState<string | null>(null);
  const settleAnimationTimerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!editingMessageId) {
      return;
    }

    const stillVisible = messages.some((message) => message.id === editingMessageId);

    if (!stillVisible) {
      setEditingMessageId(null);
      setEditingContent("");
    }
  }, [editingMessageId, messages]);

  const timelineItems = useMemo(() => buildChatTimelineItems(messages), [messages]);
  const latestUserMessageId = useMemo(() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      if (messages[index]?.role === "user") {
        return messages[index].id;
      }
    }

    return null;
  }, [messages]);

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
    userScrollIntentRef.current = false;
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

  const isActiveStream = Boolean(
    isPlaybackActive ||
      isStreaming ||
      (isStreaming && streamingToolCalls.length > 0),
  );
  const isGeneratingAnswer = isActiveStream && Boolean(streamingAnswer);
  const streamingPresentation = getPresentationPairFromToolCalls(streamingToolCalls);
  const showStreamingPresentation =
    streamingShowPresentation &&
    shouldShowRichPresentation(streamingAnswer, streamingToolCalls);
  const suppressStreamingMarkdown = shouldSuppressMarkdownForPresentation(
    streamingAnswer,
    streamingPresentation,
    streamingToolCalls,
  );
  const showStreamingCaptionReveal =
    isActiveStream &&
    suppressStreamingMarkdown &&
    Boolean(streamingAnswer?.trim()) &&
    isShortPresentationCaption(streamingAnswer, streamingToolCalls);
  const revealedStreamingCaption = useStreamingTextReveal(streamingAnswer, {
    enabled: showStreamingCaptionReveal && !isPlaybackActive,
    charsPerFrame: 3,
  });
  const streamingCaptionText =
    showStreamingCaptionReveal && isPlaybackActive
      ? streamingAnswer
      : revealedStreamingCaption;
  const streamingCaptionComplete =
    !showStreamingCaptionReveal ||
    revealedStreamingCaption.length >= String(streamingAnswer || "").length;
  const effectiveShowStreamingPresentation =
    showStreamingPresentation && streamingCaptionComplete;
  const showStreamingActivityPanel = Boolean(isStreaming || isPlaybackActive);
  const revealedStreamingAnswer = useStreamingTextReveal(streamingAnswer, {
    enabled:
      isGeneratingAnswer && !suppressStreamingMarkdown && !isPlaybackActive,
    charsPerFrame: 3,
  });

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

      userScrollIntentRef.current = false;
      pinAlignmentAppliedForRef.current = null;
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
      pinAlignmentAppliedForRef.current = null;
      followStreamRef.current = false;
      userScrollIntentRef.current = false;
      return;
    }

    if (isActiveStream && followStreamRef.current && !pinUserMessageIdRef.current) {
      requestAnimationFrame(() => {
        if (!followStreamRef.current || userScrollIntentRef.current) {
          return;
        }

        scrollToBottom("auto");
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

    const pinnedId = pinUserMessageIdRef.current;

    if (pinAlignmentAppliedForRef.current === pinnedId || userScrollIntentRef.current) {
      return;
    }

    alignPinnedUserMessage("auto");
    pinAlignmentAppliedForRef.current = pinnedId;
  }, [
    alignPinnedUserMessage,
    isLoading,
    messages,
    timelineItems.length,
  ]);

  useEffect(() => {
    if (!isActiveStream || userScrollIntentRef.current) {
      return;
    }

    const list = listRef.current;

    if (!list) {
      return;
    }

    const pinnedId = pinUserMessageIdRef.current;
    const shouldFollow = pinnedId
      ? isViewportNearResponse(list, pinnedId)
      : followStreamRef.current;

    if (!shouldFollow) {
      return;
    }

    requestAnimationFrame(() => {
      if (userScrollIntentRef.current) {
        return;
      }

      const currentList = listRef.current;

      if (!currentList) {
        return;
      }

      const streaming = currentList.querySelector(".mdc-chat-message--streaming");

      if (streaming instanceof HTMLElement) {
        scrollElementToAlignTop(currentList, streaming, 12);
        return;
      }

      if (!pinUserMessageIdRef.current && followStreamRef.current) {
        scrollElementToBottom(currentList, "auto");
      }
    });
  }, [
    isActiveStream,
    isGeneratingAnswer,
    revealedStreamingAnswer,
    streamingActivityLog,
    streamingAnswer,
    streamingStatus,
    streamingToolCalls,
  ]);

  useEffect(() => {
    if (!pendingScrollToResponseRef.current || isActiveStream) {
      return;
    }

    const list = listRef.current;

    if (!list) {
      return;
    }

    requestAnimationFrame(() => {
      const currentList = listRef.current;

      if (!currentList) {
        return;
      }

      if (scrollResponseStartIntoView(currentList)) {
        pendingScrollToResponseRef.current = false;
        updateScrollAffordances();
      }
    });
  }, [isActiveStream, messages, updateScrollAffordances]);

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
          pinAlignmentAppliedForRef.current = null;
        }
      }

      updateScrollAffordances();
    };

    const handleWheel = () => {
      userScrollIntentRef.current = true;
      followStreamRef.current = false;
    };

    const handleTouchMove = () => {
      userScrollIntentRef.current = true;
      followStreamRef.current = false;
    };

    list.addEventListener("scroll", handleScroll, { passive: true });
    list.addEventListener("wheel", handleWheel, { passive: true });
    list.addEventListener("touchmove", handleTouchMove, { passive: true });
    updateScrollAffordances();

    return () => {
      list.removeEventListener("scroll", handleScroll);
      list.removeEventListener("wheel", handleWheel);
      list.removeEventListener("touchmove", handleTouchMove);
    };
  }, [updateScrollAffordances, timelineItems.length, isActiveStream]);

  useEffect(() => {
    const wasStreaming = wasStreamingRef.current;

    if (wasStreaming && !isActiveStream) {
      const list = listRef.current;
      const pinnedId = pinUserMessageIdRef.current;
      const shouldScroll =
        list !== null &&
        (!userScrollIntentRef.current ||
          isViewportNearResponse(list, pinnedId));

      const lastAssistant = [...messages]
        .reverse()
        .find((message) => message.role === "assistant");

      if (lastAssistant?.id) {
        setEnteringAssistantId(lastAssistant.id);

        if (settleAnimationTimerRef.current !== null) {
          window.clearTimeout(settleAnimationTimerRef.current);
        }

        settleAnimationTimerRef.current = window.setTimeout(() => {
          setEnteringAssistantId(null);
          settleAnimationTimerRef.current = null;
        }, 480);
      }

      pinUserMessageIdRef.current = null;
      pinAlignmentAppliedForRef.current = null;

      if (shouldScroll) {
        userScrollIntentRef.current = false;

        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            const currentList = listRef.current;

            if (!currentList) {
              return;
            }

            if (scrollResponseStartIntoView(currentList)) {
              pendingScrollToResponseRef.current = false;
            } else {
              pendingScrollToResponseRef.current = true;
            }

            updateScrollAffordances();
          });
        });
      } else {
        userScrollIntentRef.current = false;
        updateScrollAffordances();
      }
    }

    wasStreamingRef.current = isActiveStream;
  }, [isActiveStream, messages, scrollToBottom, updateScrollAffordances]);

  useEffect(() => {
    return () => {
      if (settleAnimationTimerRef.current !== null) {
        window.clearTimeout(settleAnimationTimerRef.current);
      }
    };
  }, []);

  async function handleSaveAndResend(messageId: string) {
    const content = editingContent.trim();

    if (!content || !onEditAndResendMessage) {
      return;
    }

    setEditingMessageId(null);
    setEditingContent("");

    await onEditAndResendMessage(messageId, content);
  }

  function startEditMessage(message: ChatMessage) {
    const displayContent = resolveUserMessageContent(
      message,
      lastSentUserText,
      message.id === latestUserMessageId,
    );

    setEditingMessageId(message.id);
    setEditingContent(displayContent || message.content);
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
    const messageToolCalls = getMessageToolCalls(message);
    const messagePresentation = getPresentationPairFromToolCalls(messageToolCalls);
    const displayContent = isUser
      ? resolveUserMessageContent(
          message,
          lastSentUserText,
          message.id === latestUserMessageId,
        )
      : String(message.content ?? "").trim();
    const suppressMessageMarkdown = shouldSuppressMarkdownForPresentation(
      displayContent || message.content,
      messagePresentation,
      messageToolCalls,
    );
    const messageCanvasOpen = getCanvasOpenFromMetadata(message.metadata);

    return (
      <article
        key={message.id}
        data-message-id={message.id}
        className={`mdc-chat-message mdc-chat-message--${message.role}${
          isPending ? " mdc-chat-message--pending" : ""
        }${
          !isUser && message.id === enteringAssistantId
            ? " mdc-chat-message--settle-in"
            : ""
        }`}
      >
        <div className="mdc-chat-message-avatar" aria-hidden="true">
          {isUser ? "V" : "D"}
        </div>

        {isUser ? (
          <div
            className={`mdc-chat-message-user-stack${
              editingMessageId === message.id ? " mdc-chat-message-user-stack--editing" : ""
            }`}
          >
            {editingMessageId !== message.id ? (
              <div className="mdc-chat-message-user-toolbar">
                {message.branch && onSwitchMessageBranch ? (
                  <ChatBranchNavigator
                    branch={message.branch}
                    disabled={Boolean(isStreaming)}
                    isLoading={branchSwitchingMessageId === message.id}
                    onSelectSibling={(anchorUserMessageId) => {
                      void onSwitchMessageBranch(anchorUserMessageId, message.id);
                    }}
                  />
                ) : null}

                <div className="mdc-chat-message-actions">
                  <button
                    className="mdc-chat-message-action"
                    type="button"
                    onClick={() => void handleCopy(message.id, displayContent)}
                    aria-label={
                      copiedMessageId === message.id
                        ? "Pergunta copiada"
                        : "Copiar pergunta"
                    }
                    title={
                      copiedMessageId === message.id
                        ? "Pergunta copiada"
                        : "Copiar pergunta"
                    }
                    disabled={!displayContent.trim()}
                  >
                    {copiedMessageId === message.id ? (
                      <Check size={15} aria-hidden="true" />
                    ) : (
                      <Copy size={15} aria-hidden="true" />
                    )}
                  </button>

                  <button
                    className="mdc-chat-message-action"
                    type="button"
                    onClick={() => startEditMessage(message)}
                    disabled={Boolean(isStreaming)}
                    aria-label="Editar mensagem"
                    title="Editar e reenviar (nova variação)"
                  >
                    <Pencil size={15} aria-hidden="true" />
                  </button>

                  <button
                    className="mdc-chat-message-action"
                    type="button"
                    onClick={() => onReuseMessage?.(displayContent)}
                    aria-label="Reutilizar mensagem"
                    title="Reutilizar mensagem"
                  >
                    <RotateCcw size={15} aria-hidden="true" />
                  </button>

                  {onContinueFromMessage ? (
                    <button
                      className="mdc-chat-message-action"
                      type="button"
                      disabled={Boolean(isStreaming)}
                      onClick={() => void onContinueFromMessage(message.id)}
                      aria-label="Continuar a partir daqui"
                      title="Continuar a partir daqui (nova conversa)"
                    >
                      <GitBranch size={15} aria-hidden="true" />
                    </button>
                  ) : null}
                </div>

                {messageTime ? (
                  <time
                    className="mdc-chat-message-user-toolbar__time"
                    dateTime={message.created_at}
                  >
                    {messageTime}
                  </time>
                ) : null}
              </div>
            ) : null}

            <div
              className={`mdc-chat-message-card mdc-chat-message-card--user${
                editingMessageId === message.id
                  ? " mdc-chat-message-card--editing"
                  : ""
              }`}
            >
              {editingMessageId === message.id ? (
                <ChatMessageEditField
                  value={editingContent}
                  disabled={Boolean(isStreaming)}
                  onChange={setEditingContent}
                  onCancel={cancelEditMessage}
                  onSubmit={() => void handleSaveAndResend(message.id)}
                />
              ) : (
                <>
                  <ChatMessageAttachments
                    attachments={getMessageAttachments(message)}
                    onDownloadAttachment={onDownloadAttachment}
                  />
                  {displayContent ? (
                    <p className="mdc-chat-message-user-text">{displayContent}</p>
                  ) : null}
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="mdc-chat-message-card">
            <div className="mdc-chat-message-header">
              <strong>Minha DELPI Chat</strong>

              <div className="mdc-chat-message-meta">
                {messageTime ? (
                  <time dateTime={message.created_at}>{messageTime}</time>
                ) : null}

                <div className="mdc-chat-message-actions">
                  <button
                    className={`mdc-chat-message-action${
                      message.user_feedback === 1 ? " is-active" : ""
                    }`}
                    type="button"
                    aria-label="Resposta útil"
                    title="Resposta útil"
                    onClick={() => {
                      void (async () => {
                        if (!onMessageFeedback) {
                          return;
                        }

                        if (message.user_feedback === 1) {
                          await onMessageFeedback(message.id, null);
                          setFeedbackThanksByMessageId((current) => {
                            const next = { ...current };
                            delete next[message.id];
                            return next;
                          });
                          return;
                        }

                        const result = await onMessageFeedback(message.id, 1);
                        const thanksMessage =
                          result && "thanksMessage" in result
                            ? result.thanksMessage
                            : undefined;

                        if (thanksMessage) {
                          setFeedbackThanksByMessageId((current) => ({
                            ...current,
                            [message.id]: thanksMessage,
                          }));
                          setFeedbackReasonPickerFor(null);
                        }
                      })();
                    }}
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
                    onClick={() => {
                      void (async () => {
                        if (!onMessageFeedback) {
                          return;
                        }

                        if (message.user_feedback === -1) {
                          await onMessageFeedback(message.id, null);
                          setFeedbackReasonPickerFor(null);
                          setFeedbackThanksByMessageId((current) => {
                            const next = { ...current };
                            delete next[message.id];
                            return next;
                          });
                          return;
                        }

                        await onMessageFeedback(message.id, -1);
                        setFeedbackReasonPickerFor(message.id);
                        setFeedbackThanksByMessageId((current) => {
                          const next = { ...current };
                          delete next[message.id];
                          return next;
                        });
                      })();
                    }}
                  >
                    <ThumbsDown size={15} aria-hidden="true" />
                  </button>

                  <button
                    className="mdc-chat-message-action"
                    type="button"
                    onClick={() =>
                      void handleCopy(
                        message.id,
                        buildAssistantCopyText(message.content, messageToolCalls),
                      )
                    }
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

                  {onContinueFromMessage ? (
                    <button
                      className="mdc-chat-message-action"
                      type="button"
                      disabled={Boolean(isStreaming)}
                      onClick={() => void onContinueFromMessage(message.id)}
                      aria-label="Continuar a partir daqui"
                      title="Continuar a partir daqui (nova conversa)"
                    >
                      <GitBranch size={15} aria-hidden="true" />
                    </button>
                  ) : null}
                </div>
              </div>
            </div>

            {isAssistantGenerating(message) ? (
              <div className="mdc-chat-thinking" role="status" aria-live="polite">
                <span className="mdc-chat-thinking__dot" />
                <span className="mdc-chat-thinking__dot" />
                <span className="mdc-chat-thinking__dot" />
                <p>Gerando resposta...</p>
              </div>
            ) : (
              <>
                <ChatMessageAttachments
                  attachments={getMessageAttachments(message)}
                  onDownloadAttachment={onDownloadAttachment}
                />
                {shouldShowRichPresentation(displayContent, messageToolCalls)
                  ? renderPresentation(
                      messageToolCalls,
                      displayContent,
                      onDrillDown,
                    )
                  : null}
                {suppressMessageMarkdown || !displayContent ? null : (
                  <ChatMarkdown content={displayContent} />
                )}
                {messageCanvasOpen ? (
                  <ChatInlineCanvas
                    payload={messageCanvasOpen}
                    onOpen={onOpenCanvas}
                  />
                ) : null}
              </>
            )}

            {!isAssistantGenerating(message) ? (
              <>
                {!shouldShowActionResults(displayContent, messageToolCalls) ? null : (
                  <ChatActionResults toolCalls={messageToolCalls} />
                )}
                <ChatAdminDebugPanel
                  debug={
                    (message.metadata?.adminDebug as Record<
                      string,
                      unknown
                    > | null) ?? null
                  }
                />
                <ChatTrustBadges
                  signals={
                    (message.metadata?.trustSignals as
                      | ChatTrustSignal[]
                      | undefined) ?? []
                  }
                />
                <ChatActionConfirmationPanel
                  confirmation={
                    message.metadata?.actionConfirmation as
                      | ChatActionConfirmation
                      | undefined
                  }
                  onUseQuery={onDrillDown ?? onReuseMessage}
                />
                <ChatSources
                  sources={filterVisibleChatSources(getMessageSources(message))}
                  webSearchResearch={getWebSearchResearch(message)}
                />
                <ChatFollowUpChips
                  suggestions={
                    (message.metadata?.followUpSuggestions as
                      | ChatFollowUpSuggestion[]
                      | undefined) ?? []
                  }
                  onUseSuggestion={onDrillDown}
                />
                <ChatFollowUpChips
                  suggestions={
                    (message.metadata?.webSearchFollowUpSuggestions as
                      | ChatFollowUpSuggestion[]
                      | undefined) ?? []
                  }
                  onUseSuggestion={onDrillDown}
                  groupLabel="Após pesquisa web"
                  ariaLabel="Ações sugeridas após pesquisa na internet"
                />
                <ChatFollowUpChips
                  suggestions={
                    (message.metadata?.helpFollowUpSuggestions as
                      | ChatFollowUpSuggestion[]
                      | undefined) ?? []
                  }
                  onUseSuggestion={onDrillDown}
                  groupLabel="Explorar"
                  ariaLabel="Sugestões para explorar o chat"
                />
                <ChatFollowUpChips
                  suggestions={
                    (message.metadata?.attachmentFollowUpSuggestions as
                      | ChatFollowUpSuggestion[]
                      | undefined) ?? []
                  }
                  onUseSuggestion={onDrillDown}
                  groupLabel="Com o anexo"
                  ariaLabel="Ações sugeridas para o arquivo anexado"
                />
                <ChatMessageFeedbackPanel
                  thanksMessage={feedbackThanksByMessageId[message.id]}
                  showReasonPicker={feedbackReasonPickerFor === message.id}
                  onPickReason={(reasonId) => {
                    void (async () => {
                      await onMessageFeedback?.(message.id, -1, reasonId);
                      setFeedbackReasonPickerFor(null);
                    })();
                  }}
                  onDismissReasons={() => setFeedbackReasonPickerFor(null)}
                />
              </>
            ) : null}
          </div>
        )}
      </article>
    );
  }

  if (isLoading) {
    return (
      <div className="mdc-chat-message-list-wrap">
        <div className="mdc-chat-message-list mdc-chat-message-list__inner" aria-live="polite">
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
    return (
      <ChatEmptyState />
    );
  }

  return (
    <div
      ref={listRef}
      className={[
        "mdc-chat-message-list-wrap",
        isActiveStream ? "mdc-chat-message-list-wrap--streaming" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div
        className="mdc-chat-message-list mdc-chat-message-list__inner"
        aria-live="polite"
      >
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

              <div
                className={[
                  "mdc-chat-message-streaming-body",
                  effectiveShowStreamingPresentation
                    ? "mdc-chat-message-streaming-body--has-presentation"
                    : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {showStreamingActivityPanel ||
                (streamingAnswer &&
                  !suppressStreamingMarkdown &&
                  !showStreamingCaptionReveal) ? (
                  <div className="mdc-chat-streaming-overlay">
                    {showStreamingActivityPanel ? (
                      <ChatStreamingActivityPanel
                        status={streamingStatus}
                        entries={streamingActivityLog}
                        isActive
                        isAnswering={Boolean(streamingAnswer?.trim())}
                      />
                    ) : null}
                    {streamingAnswer &&
                    !suppressStreamingMarkdown &&
                    !showStreamingCaptionReveal ? (
                      <div
                        className={[
                          "mdc-chat-stream-answer",
                          isGeneratingAnswer ? "is-visible" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                      >
                        <ChatMarkdown content={revealedStreamingAnswer} />
                      </div>
                    ) : null}
                  </div>
                ) : null}
                {showStreamingCaptionReveal ? (
                  <div
                    className={[
                      "mdc-chat-stream-caption",
                      streamingCaptionText ? "is-visible" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    <h3 className="mdc-rich-presentation__heading">
                      {streamingCaptionText}
                    </h3>
                  </div>
                ) : null}
                {effectiveShowStreamingPresentation ? (
                  <div className="mdc-chat-stream-presentation is-visible">
                    {renderPresentation(
                      streamingToolCalls,
                      streamingAnswer,
                      onDrillDown,
                    )}
                  </div>
                ) : null}
                {streamingCanvasOpen ? (
                  <ChatInlineCanvas
                    payload={streamingCanvasOpen}
                    onOpen={onOpenCanvas}
                  />
                ) : null}
              </div>
              {showStreamingPresentation &&
              shouldShowActionResults(streamingAnswer, streamingToolCalls) ? (
                <div className="mdc-chat-stream-extras is-visible">
                  <ChatActionResults toolCalls={streamingToolCalls} />
                </div>
              ) : null}
              <ChatAdminDebugPanel
                debug={(streamingAdminDebug as Record<string, unknown> | null) ?? null}
              />
              {filterVisibleChatSources(streamingSources).length > 0 ? (
                <div className="mdc-chat-stream-extras is-visible">
                  <ChatSources sources={filterVisibleChatSources(streamingSources)} />
                </div>
              ) : null}
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
