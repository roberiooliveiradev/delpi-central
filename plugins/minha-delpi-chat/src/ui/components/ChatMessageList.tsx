import {
  ArrowDown,
  BookmarkPlus,
  Check,
  Copy,
  Download,
  FileText,
  GitBranch,
  Image as ImageIcon,
  MessagesSquare,
  Pencil,
  RotateCcw,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { useStreamingTextReveal } from "../../state/hooks/useStreamingTextReveal";
import { useChatFeedbackReasons } from "../../state/hooks/useChatFeedbackReasons";
import { attachmentReadingStatusLabel } from "../chatAttachmentStatus";

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
import { ChatInteractivityBlock } from "./ChatInteractivityBlock";
import { ChatGuidedFlowBlock } from "./ChatGuidedFlowBlock";
import { ChatMilestoneCelebration } from "./ChatMilestoneCelebration";
import type { ChatGuidedFlow, ChatGuidedFlowCard } from "../../data/api/chatTypes";
import { ChatMessageFeedbackPanel } from "./ChatMessageFeedbackPanel";
import {
  ChatHelpSelfHelpFeedback,
  type HelpSelfHelpFeedbackPayload,
} from "./ChatHelpSelfHelpFeedback";
import { ChatAssistantContent } from "./ChatAssistantContent";
import { ChatMarkdown } from "./ChatMarkdown";
import {
  downloadDrawingAnalysisCsv,
  downloadDrawingAnalysisMarkdown,
  downloadDrawingAnalysisPdf,
  downloadDrawingAnalysisXlsx,
} from "../utils/drawingAnalysisExport";
import { ChatActionResults } from "./ChatActionResults";
import { ChatAdminDebugPanel } from "./ChatAdminDebugPanel";
import { isAssistantGenerating } from "../../state/chatMessageDelivery";
import { ChatAssistantMessageMenu } from "./ChatAssistantMessageMenu";
import {
  messageHasChartPresentation,
  messageHasDashboardPresentation,
} from "./chartExplain";
import {
  buildAssistantCopyText,
  buildEmailCopyText,
  getPresentationPairFromToolCalls,
  getTextMarkdownFromToolCalls,
  isShortPresentationCaption,
  shouldShowActionResults,
  shouldSuppressMarkdownForPresentation,
} from "./chatPresentation";
import {
  resolveAssistantStreamingProseState,
  shouldBypassIncrementalTextReveal,
} from "./assistantProseRendering";
import { ChatSources } from "./ChatSources";
import { ChatTrustBadges, type ChatTrustSignal } from "./ChatTrustBadges";
import {
  ChatActionConfirmationPanel,
  type ChatActionConfirmation,
} from "./ChatActionConfirmationPanel";
import { ChatStreamingActivityPanel } from "./ChatStreamingActivityPanel";
import { ChatInlineCanvas } from "./ChatInlineCanvas";
import { resolveUserMessageTurnContextChips } from "../../state/chatComposerContext";
import { ChatMessageEditField } from "./ChatMessageEditField";
import { ChatUserTurnContextChips } from "./ChatUserTurnContextChips";
import { ChatErrorHandlingCard } from "./ChatErrorHandlingCard";
import { enrichCanvasOpenFromSessionMetadata, getCanvasOpenFromMetadata } from "./chatCanvas";
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
  ) => Promise<{
    thanksMessage?: string;
    correctiveActions?: Array<{
      id: string;
      label: string;
      action: string;
      query?: string;
    }>;
  } | void>;
  onDownloadAttachment?: (attachmentId: string) => Promise<void>;
  onSwitchMessageBranch?: (
    anchorUserMessageId: string,
    sourceUserMessageId: string,
  ) => Promise<void>;
  branchSwitchingMessageId?: string | null;
  onContinueFromMessage?: (messageId: string) => Promise<void>;
  onAddMessageToContext?: (message: ChatMessage) => void;
  onAddMessageTurnToContext?: (answerMessage: ChatMessage) => void;
  lastSentUserText?: string;
  onRecordHelpEvent?: (payload: {
    event: string;
    metadata?: Record<string, unknown> | null;
  }) => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
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

type MessageAttachment = {
  id?: string;
  filename?: string;
  original_filename?: string;
  content_type?: string | null;
  size_bytes?: number;
  status?: string;
  parsed?: boolean;
  readingStatus?: string;
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
        const readingStatus =
          attachment.readingStatus ||
          attachmentReadingStatusLabel(attachment.status, attachment.parsed);
        const isImage = String(attachment.content_type || "").startsWith("image/");

        return (
          <span
            key={attachment.id || `${filename}-${index}`}
            className="mdc-chat-message-attachment"
            title={filename}
          >
            {isImage ? (
              <ImageIcon size={14} aria-hidden="true" />
            ) : (
              <FileText size={14} aria-hidden="true" />
            )}
            <strong>{filename}</strong>
            {size ? <small>{size}</small> : null}
            <small className="mdc-chat-message-attachment__status">{readingStatus}</small>
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
  streamingToolCalls = [],
  streamingAdminDebug,
  streamingStatus,
  streamingActivityLog = [],
  streamingShowPresentation: _streamingShowPresentation = true,
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
  onAddMessageToContext,
  onAddMessageTurnToContext,
  onOpenCanvas,
  lastSentUserText = "",
  onRecordHelpEvent,
  getAccessToken,
}: ChatMessageListProps) {
  const { reasons: feedbackReasons, primaryReasonIds: feedbackPrimaryReasonIds } =
    useChatFeedbackReasons({ getAccessToken });
  const [feedbackThanksByMessageId, setFeedbackThanksByMessageId] = useState<
    Record<string, string>
  >({});
  const [feedbackReasonPickerFor, setFeedbackReasonPickerFor] = useState<string | null>(
    null,
  );
  const [feedbackExtendedReasonsFor, setFeedbackExtendedReasonsFor] = useState<
    string | null
  >(null);
  const [feedbackCorrectiveByMessageId, setFeedbackCorrectiveByMessageId] = useState<
    Record<
      string,
      Array<{
        id: string;
        label: string;
        action: string;
        query?: string;
      }>
    >
  >({});
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

  const [inlineExplainMessageId, setInlineExplainMessageId] = useState<string | null>(null);
  const [inlineExplainKind, setInlineExplainKind] = useState<"chart" | "dashboard" | null>(
    null,
  );
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
  const timelineItems = useMemo(() => {
    const visibleMessages = isActiveStream
      ? messages.filter((message) => !isAssistantGenerating(message))
      : messages;

    return buildChatTimelineItems(visibleMessages);
  }, [isActiveStream, messages]);
  const isGeneratingAnswer = isActiveStream && Boolean(streamingAnswer);
  const streamingPresentation = getPresentationPairFromToolCalls(streamingToolCalls);
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
  const showStreamingActivityPanel = Boolean(
    (isStreaming || isPlaybackActive) && !streamingAnswer?.trim(),
  );
  const revealedStreamingAnswer = useStreamingTextReveal(streamingAnswer, {
    enabled:
      isGeneratingAnswer &&
      !suppressStreamingMarkdown &&
      !isPlaybackActive &&
      !shouldBypassIncrementalTextReveal(streamingAnswer),
    charsPerFrame: 3,
  });
  const streamingProseState = resolveAssistantStreamingProseState({
    answer: streamingAnswer,
    revealedAnswer: revealedStreamingAnswer,
    suppressRichPresentation: suppressStreamingMarkdown,
    isGenerating: isGeneratingAnswer,
    isPlayback: isPlaybackActive,
  });
  const streamingMarkdownContent = streamingProseState.markdownContent;

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
    const displayContent = isUser
      ? resolveUserMessageContent(
          message,
          lastSentUserText,
          message.id === latestUserMessageId,
        )
      : String(message.content ?? "").trim() ||
        getTextMarkdownFromToolCalls(messageToolCalls);
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

                  {onAddMessageToContext ? (
                    <button
                      className="mdc-chat-message-action"
                      type="button"
                      disabled={Boolean(isStreaming) || !displayContent.trim()}
                      onClick={() => onAddMessageToContext(message)}
                      aria-label="Adicionar pergunta ao contexto"
                      title="Adicionar pergunta ao contexto"
                    >
                      <BookmarkPlus size={15} aria-hidden="true" />
                    </button>
                  ) : null}

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
                  <ChatUserTurnContextChips
                    chips={resolveUserMessageTurnContextChips(
                      message.metadata as Record<string, unknown> | null | undefined,
                    )}
                  />
                  <ChatMessageAttachments
                    attachments={getMessageAttachments(message)}
                    onDownloadAttachment={onDownloadAttachment}
                  />
                  {displayContent ? (
                    <div className="mdc-chat-message-user-text">
                      <ChatMarkdown content={displayContent} compact softBreaks />
                    </div>
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

                {!isAssistantGenerating(message) ? (
                <div className="mdc-chat-message-actions">
                  {onDrillDown && messageToolCalls.length > 0 ? (
                    <ChatAssistantMessageMenu
                      toolCalls={messageToolCalls}
                      disabled={Boolean(isStreaming)}
                      onSelect={onDrillDown}
                    />
                  ) : null}

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

                  {onAddMessageToContext ? (
                    <button
                      className="mdc-chat-message-action"
                      type="button"
                      disabled={Boolean(isStreaming) || !displayContent.trim()}
                      onClick={() => onAddMessageToContext(message)}
                      aria-label="Adicionar resposta ao contexto"
                      title="Adicionar resposta ao contexto"
                    >
                      <BookmarkPlus size={15} aria-hidden="true" />
                    </button>
                  ) : null}

                  {onAddMessageTurnToContext ? (
                    <button
                      className="mdc-chat-message-action"
                      type="button"
                      disabled={Boolean(isStreaming) || !displayContent.trim()}
                      onClick={() => onAddMessageTurnToContext(message)}
                      aria-label="Adicionar pergunta e resposta ao contexto"
                      title="Adicionar pergunta e resposta ao contexto"
                    >
                      <MessagesSquare size={15} aria-hidden="true" />
                    </button>
                  ) : null}

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
                ) : null}
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
                {displayContent || messageToolCalls.length ? (
                  <ChatAssistantContent
                    content={displayContent}
                    toolCalls={messageToolCalls}
                    onDrillDown={onDrillDown}
                    onOpenCanvas={onOpenCanvas}
                    requestChartExplanation={
                      inlineExplainMessageId === message.id &&
                      inlineExplainKind === "chart"
                    }
                    onChartExplanationHandled={() => {
                      setInlineExplainMessageId(null);
                      setInlineExplainKind(null);
                    }}
                  />
                ) : null}
                {messageCanvasOpen ? (
                  <ChatInlineCanvas
                    payload={messageCanvasOpen}
                    onOpen={
                      onOpenCanvas
                        ? (payload) =>
                            onOpenCanvas(
                              enrichCanvasOpenFromSessionMetadata(
                                payload,
                                message.metadata,
                              ),
                            )
                        : undefined
                    }
                  />
                ) : null}
              </>
            )}

            {!isAssistantGenerating(message) ? (
              <>
                {!shouldShowActionResults(displayContent, messageToolCalls) ? null : (
                  <ChatActionResults toolCalls={messageToolCalls} />
                )}
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
                {message.metadata?.errorHandling ? (
                  <ChatErrorHandlingCard
                    metadata={message.metadata}
                    onUseSuggestion={onDrillDown}
                    showRecoveryChips={!message.metadata?.interactivity?.consolidated}
                  />
                ) : null}
                {message.metadata?.interactivity?.consolidated ? (
                  <ChatInteractivityBlock
                    interactivity={message.metadata.interactivity}
                    variant={message.metadata?.errorHandling ? "recovery" : "default"}
                    onUseSuggestion={onDrillDown}
                    onExplainChart={
                      messageHasChartPresentation(messageToolCalls)
                        ? () => {
                            setInlineExplainMessageId(message.id);
                            setInlineExplainKind("chart");
                          }
                        : undefined
                    }
                    onExplainDashboard={
                      messageHasDashboardPresentation(messageToolCalls)
                        ? () => {
                            setInlineExplainMessageId(message.id);
                            setInlineExplainKind("dashboard");
                          }
                        : undefined
                    }
                    onRecordClick={({ label, query, group }) => {
                      onRecordHelpEvent?.({
                        event: "interactivity_suggestion_clicked",
                        metadata: {
                          label,
                          query,
                          group: group ?? null,
                          messageId: message.id,
                          sessionId: conversationKey ?? null,
                        },
                      });
                    }}
                  />
                ) : (
                  <>
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
                  </>
                )}
                {!message.metadata?.interactivity?.consolidated ? (
                <ChatFollowUpChips
                  suggestions={
                    (message.metadata?.helpFollowUpSuggestions as
                      | ChatFollowUpSuggestion[]
                      | undefined) ?? []
                  }
                  onUseSuggestion={(query) => {
                    const helpSuggestions =
                      (message.metadata?.helpFollowUpSuggestions as
                        | ChatFollowUpSuggestion[]
                        | undefined) ?? [];
                    const match = helpSuggestions.find((item) => item.query === query);
                    const helpSelfHelp = message.metadata?.helpSelfHelp as
                      | { topic?: string }
                      | undefined;

                    onRecordHelpEvent?.({
                      event: "self_help_suggestion_clicked",
                      metadata: {
                        query,
                        label: match?.label ?? null,
                        topic: helpSelfHelp?.topic ?? null,
                        messageId: message.id,
                      },
                    });
                    onDrillDown?.(query);
                  }}
                  groupLabel="Explorar"
                  ariaLabel="Sugestões para explorar o chat"
                />
                ) : null}
                {message.metadata?.helpSelfHelp ? (
                  <ChatHelpSelfHelpFeedback
                    topic={
                      (message.metadata.helpSelfHelp as { topic?: string } | undefined)?.topic ??
                      null
                    }
                    onFeedback={(payload: HelpSelfHelpFeedbackPayload) => {
                      onRecordHelpEvent?.({
                        event: "self_help_feedback",
                        metadata: {
                          helpful: payload.helpful,
                          reasonId: payload.reasonId ?? null,
                          topic: payload.topic ?? null,
                          messageId: message.id,
                        },
                      });
                    }}
                  />
                ) : null}
                {!message.metadata?.interactivity?.consolidated ? (
                  <ChatFollowUpChips
                    suggestions={
                      (message.metadata?.routingDisambiguationSuggestions as
                        | ChatFollowUpSuggestion[]
                        | undefined) ?? []
                    }
                    onUseSuggestion={onDrillDown}
                    groupLabel="Sobre o produto"
                    ariaLabel="Escolha o que consultar sobre o produto"
                  />
                ) : null}
                {message.metadata?.interactivity?.consolidated ? null : (
                  <ChatMilestoneCelebration
                    celebrations={
                      (message.metadata?.milestoneCelebrations as
                        | { id: string; label?: string; message: string }[]
                        | undefined) ?? []
                    }
                  />
                )}
                {!message.metadata?.interactivity?.consolidated ? (
                  <ChatFollowUpChips
                    suggestions={
                      (message.metadata?.onboardingFollowUpSuggestions as
                        | ChatFollowUpSuggestion[]
                        | undefined) ?? []
                    }
                    onUseSuggestion={onDrillDown}
                    groupLabel="Primeiros passos"
                    ariaLabel="Sugestões do guia de uso"
                  />
                ) : null}
                <ChatGuidedFlowBlock
                  flow={message.metadata?.guidedFlow as ChatGuidedFlow | undefined}
                  cards={message.metadata?.guidedFlowCards as ChatGuidedFlowCard[] | undefined}
                  suggestions={
                    (message.metadata?.guidedFlowSuggestions as
                      | ChatFollowUpSuggestion[]
                      | undefined) ?? []
                  }
                  onUseQuery={onDrillDown}
                />
                {!message.metadata?.interactivity?.consolidated &&
                !message.metadata?.errorHandling ? (
                  <ChatFollowUpChips
                    suggestions={
                      (message.metadata?.helpErrorFollowUpSuggestions as
                        | ChatFollowUpSuggestion[]
                        | undefined) ?? []
                    }
                    onUseSuggestion={onDrillDown}
                    groupLabel="Ajuda após erro"
                    ariaLabel="Sugestões de ajuda após falha na consulta"
                  />
                ) : null}
                {!message.metadata?.interactivity?.consolidated ? (
                  <>
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
                    <ChatFollowUpChips
                      suggestions={
                        (message.metadata?.canvasFollowUpSuggestions as
                          | ChatFollowUpSuggestion[]
                          | undefined) ?? []
                      }
                      onUseSuggestion={onDrillDown}
                      groupLabel="Na lousa"
                      ariaLabel="Ações sugeridas para a lousa"
                    />
                  </>
                ) : null}
                {message.metadata?.attachmentSourceCitation?.note ? (
                  <p className="mdc-chat-source-citation">
                    {String(message.metadata.attachmentSourceCitation.note)}
                  </p>
                ) : null}
                {message.metadata?.drawingAnalysisExport?.markdown ? (
                  <div className="mdc-chat-drawing-export">
                    <button
                      type="button"
                      className="mdc-chat-message-action mdc-chat-drawing-export__btn"
                      onClick={() =>
                        void downloadDrawingAnalysisPdf(
                          message.metadata!.drawingAnalysisExport!,
                          message.metadata?.drawingAnalysis as
                            | Record<string, unknown>
                            | undefined,
                        )
                      }
                      aria-label="Baixar relatório PDF"
                      title="Baixar relatório (.pdf)"
                    >
                      <Download size={15} aria-hidden="true" />
                      <span>PDF</span>
                    </button>
                    <button
                      type="button"
                      className="mdc-chat-message-action mdc-chat-drawing-export__btn"
                      onClick={() =>
                        downloadDrawingAnalysisMarkdown(
                          message.metadata!.drawingAnalysisExport!,
                        )
                      }
                      aria-label="Baixar relatório Markdown"
                      title="Baixar relatório (.md)"
                    >
                      <Download size={15} aria-hidden="true" />
                      <span>MD</span>
                    </button>
                    {message.metadata.drawingAnalysisExport.csv ? (
                      <button
                        type="button"
                        className="mdc-chat-message-action mdc-chat-drawing-export__btn"
                        onClick={() =>
                          downloadDrawingAnalysisCsv(
                            message.metadata!.drawingAnalysisExport!,
                          )
                        }
                        aria-label="Baixar não conformidades CSV"
                        title="Baixar não conformidades (.csv)"
                      >
                        <Download size={15} aria-hidden="true" />
                        <span>CSV</span>
                      </button>
                    ) : null}
                    {(message.metadata.drawingAnalysisExport.spreadsheetRows?.length ?? 0) >
                    0 ? (
                      <button
                        type="button"
                        className="mdc-chat-message-action mdc-chat-drawing-export__btn"
                        onClick={() =>
                          void downloadDrawingAnalysisXlsx(
                            message.metadata!.drawingAnalysisExport!,
                          )
                        }
                        aria-label="Baixar não conformidades XLSX"
                        title="Baixar não conformidades (.xlsx)"
                      >
                        <Download size={15} aria-hidden="true" />
                        <span>XLSX</span>
                      </button>
                    ) : null}
                  </div>
                ) : null}
                {!message.metadata?.interactivity?.consolidated ? (
                  <>
                    <ChatFollowUpChips
                      suggestions={
                        (message.metadata?.drawingFollowUpSuggestions as
                          | ChatFollowUpSuggestion[]
                          | undefined) ?? []
                      }
                      onUseSuggestion={onDrillDown}
                      groupLabel="Análise de desenho"
                      ariaLabel="Ações sugeridas após análise de desenho técnico"
                    />
                    <ChatFollowUpChips
                      suggestions={
                        (message.metadata?.textCorrectionFollowUpSuggestions as
                          | ChatFollowUpSuggestion[]
                          | undefined) ?? []
                      }
                      onUseSuggestion={onDrillDown}
                      groupLabel="Refinar texto"
                      ariaLabel="Ações sugeridas após correção de texto"
                    />
                    <ChatFollowUpChips
                      suggestions={
                        (message.metadata?.textTaskFollowUpSuggestions as
                          | ChatFollowUpSuggestion[]
                          | undefined) ?? []
                      }
                      onUseSuggestion={onDrillDown}
                      groupLabel="Refinar texto"
                      ariaLabel="Sugestões para tarefas textuais"
                    />
                    <ChatFollowUpChips
                      suggestions={
                        (message.metadata?.emailFollowUpSuggestions as
                          | ChatFollowUpSuggestion[]
                          | undefined) ?? []
                      }
                      onUseSuggestion={onDrillDown}
                      groupLabel="Refinar e-mail"
                      ariaLabel="Ações sugeridas após geração de e-mail"
                    />
                  </>
                ) : null}
                {(message.metadata?.emailPreferences?.labels?.length ?? 0) > 0 ? (
                  <p className="mdc-chat-message-list__email-meta" role="note">
                    Preferências de e-mail:{" "}
                    {(message.metadata!.emailPreferences!.labels as string[]).join(" · ")}
                  </p>
                ) : null}
                {(message.metadata?.textCorrectionPreferences?.labels?.length ?? 0) > 0 ? (
                  <p className="mdc-chat-message-list__email-meta" role="note">
                    Preferências de correção:{" "}
                    {(message.metadata!.textCorrectionPreferences!.labels as string[]).join(
                      " · ",
                    )}
                  </p>
                ) : null}
                {message.metadata?.emailDataSource?.title ? (
                  <p className="mdc-chat-message-list__email-meta" role="note">
                    Fonte dos dados: {String(message.metadata.emailDataSource.title)}
                    {message.metadata.emailDataSource.path
                      ? ` (${String(message.metadata.emailDataSource.path)})`
                      : ""}
                  </p>
                ) : null}
                {(message.metadata?.textTask as { type?: string } | undefined)?.type ===
                "email" ? (
                  <div className="mdc-chat-drawing-export">
                    <button
                      type="button"
                      className="mdc-chat-message-action mdc-chat-drawing-export__btn"
                      onClick={() =>
                        void handleCopy(
                          message.id,
                          buildEmailCopyText(message.content),
                        )
                      }
                      aria-label={
                        copiedMessageId === message.id
                          ? "E-mail copiado"
                          : "Copiar e-mail"
                      }
                      title={
                        copiedMessageId === message.id
                          ? "E-mail copiado"
                          : "Copiar e-mail (assunto e corpo)"
                      }
                    >
                      {copiedMessageId === message.id ? (
                        <Check size={15} aria-hidden="true" />
                      ) : (
                        <Copy size={15} aria-hidden="true" />
                      )}
                      <span>E-mail</span>
                    </button>
                  </div>
                ) : null}
                {(message.metadata?.textTask as { type?: string } | undefined)?.type ===
                "correction" ? (
                  <div className="mdc-chat-drawing-export">
                    <button
                      type="button"
                      className="mdc-chat-message-action mdc-chat-drawing-export__btn"
                      onClick={() => void handleCopy(message.id, message.content)}
                      aria-label={
                        copiedMessageId === message.id
                          ? "Texto copiado"
                          : "Copiar texto corrigido"
                      }
                      title={
                        copiedMessageId === message.id
                          ? "Texto copiado"
                          : "Copiar versão corrigida"
                      }
                    >
                      {copiedMessageId === message.id ? (
                        <Check size={15} aria-hidden="true" />
                      ) : (
                        <Copy size={15} aria-hidden="true" />
                      )}
                      <span>Texto</span>
                    </button>
                  </div>
                ) : null}
                <ChatMessageFeedbackPanel
                  reasons={feedbackReasons}
                  primaryReasonIds={feedbackPrimaryReasonIds}
                  thanksMessage={feedbackThanksByMessageId[message.id]}
                  showReasonPicker={feedbackReasonPickerFor === message.id}
                  showExtendedReasons={feedbackExtendedReasonsFor === message.id}
                  correctiveActions={feedbackCorrectiveByMessageId[message.id]}
                  onPickReason={(reasonId) => {
                    void (async () => {
                      const result = await onMessageFeedback?.(message.id, -1, reasonId);
                      setFeedbackReasonPickerFor(null);
                      setFeedbackExtendedReasonsFor(null);

                      if (
                        result &&
                        "correctiveActions" in result &&
                        result.correctiveActions?.length
                      ) {
                        setFeedbackCorrectiveByMessageId((current) => ({
                          ...current,
                          [message.id]: result.correctiveActions ?? [],
                        }));
                      }
                    })();
                  }}
                  onShowExtendedReasons={() => setFeedbackExtendedReasonsFor(message.id)}
                  onDismissReasons={() => {
                    setFeedbackReasonPickerFor(null);
                    setFeedbackExtendedReasonsFor(null);
                  }}
                  onCorrectiveAction={(action) => {
                    if (action.action === "dismiss") {
                      setFeedbackCorrectiveByMessageId((current) => {
                        const next = { ...current };
                        delete next[message.id];
                        return next;
                      });
                      return;
                    }

                    if (action.query && onDrillDown) {
                      onDrillDown(action.query);
                    }

                    onRecordHelpEvent?.({
                      event: "feedback_corrective_clicked",
                      metadata: {
                        messageId: message.id,
                        actionId: action.id,
                        reason: message.user_feedback_reason,
                      },
                    });

                    setFeedbackCorrectiveByMessageId((current) => {
                      const next = { ...current };
                      delete next[message.id];
                      return next;
                    });
                  }}
                  onDismissCorrective={() => {
                    setFeedbackCorrectiveByMessageId((current) => {
                      const next = { ...current };
                      delete next[message.id];
                      return next;
                    });
                  }}
                />
                <ChatAdminDebugPanel
                  debug={
                    (message.metadata?.adminDebug as Record<
                      string,
                      unknown
                    > | null) ?? null
                  }
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
                  streamingToolCalls.length > 0
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
                    !showStreamingCaptionReveal &&
                    streamingMarkdownContent ? (
                      <div
                        className={[
                          "mdc-chat-stream-answer",
                          isGeneratingAnswer ? "is-visible" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                      >
                        <ChatAssistantContent
                          content={streamingMarkdownContent}
                          toolCalls={streamingToolCalls}
                          onDrillDown={onDrillDown}
                          onOpenCanvas={onOpenCanvas}
                        />
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
                    {streamingProseState.captionUsesMarkdown ? (
                      <ChatMarkdown content={streamingCaptionText} compact />
                    ) : (
                      <h3 className="mdc-rich-presentation__heading">
                        {streamingCaptionText}
                      </h3>
                    )}
                  </div>
                ) : null}
                {streamingAnswer &&
                suppressStreamingMarkdown &&
                !showStreamingCaptionReveal &&
                streamingCaptionComplete ? (
                  <div className="mdc-chat-stream-presentation is-visible">
                    <ChatAssistantContent
                      content={streamingAnswer}
                      toolCalls={streamingToolCalls}
                      onDrillDown={onDrillDown}
                      onOpenCanvas={onOpenCanvas}
                    />
                  </div>
                ) : null}
                {streamingCanvasOpen ? (
                  <ChatInlineCanvas
                    payload={streamingCanvasOpen}
                    onOpen={onOpenCanvas}
                  />
                ) : null}
              </div>
              {shouldShowActionResults(streamingAnswer, streamingToolCalls) ? (
                <div className="mdc-chat-stream-extras is-visible">
                  <ChatActionResults toolCalls={streamingToolCalls} />
                </div>
              ) : null}
              {filterVisibleChatSources(streamingSources).length > 0 ? (
                <div className="mdc-chat-stream-extras is-visible">
                  <ChatSources sources={filterVisibleChatSources(streamingSources)} />
                </div>
              ) : null}
              <ChatAdminDebugPanel
                debug={(streamingAdminDebug as Record<string, unknown> | null) ?? null}
              />
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
