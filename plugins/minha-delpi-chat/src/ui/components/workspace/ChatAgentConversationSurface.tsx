import type { ReactNode } from "react";

import type { ChatAgent, ChatMessage, ChatStreamActivityEntry, ChatToolCall } from "../../../data/api/chatTypes";
import type { ChatComposerBindings } from "../../../state/hooks/useChatComposerBindings";
import { ChatInput } from "../composer/ChatInput";
import { ChatMessageList } from "../message/ChatMessageList";
import { ChatAgentHome } from "./ChatAgentHome";

import "./ChatAgentConversationSurface.css";

type ChatAgentConversationSurfaceProps = {
  agent: ChatAgent;
  messages: ChatMessage[];
  draft: string;
  isSending: boolean;
  isConversationEmpty: boolean;
  composerBindings: ChatComposerBindings;
  onDraftChange: (value: string) => void;
  onSubmit: () => void;
  onCancel?: () => void;
  onIcebreaker: (query: string) => void;
  defaultIcebreakersHint?: string | null;
  canManageAgent?: boolean;
  onManageAgent?: () => void;
  conversationKey?: string | null;
  streamingStatus?: string;
  streamingAnswer?: string;
  streamingToolCalls?: ChatToolCall[];
  streamingActivityLog?: ChatStreamActivityEntry[];
  composerFooter?: ReactNode;
  messageList?: ReactNode;
};

export function ChatAgentConversationSurface({
  agent,
  messages,
  draft,
  isSending,
  isConversationEmpty,
  composerBindings,
  onDraftChange,
  onSubmit,
  onCancel,
  onIcebreaker,
  defaultIcebreakersHint,
  canManageAgent = false,
  onManageAgent,
  conversationKey,
  streamingStatus,
  streamingAnswer = "",
  streamingToolCalls = [],
  streamingActivityLog = [],
  composerFooter,
  messageList,
}: ChatAgentConversationSurfaceProps) {
  const {
    placeholder,
    composerAttachmentProps,
    composerPresentationFormatProps,
    composerResponseModeProps,
    composerTypingCorrectionProps,
    composerContextProps,
  } = composerBindings;

  const typingCorrectionProps = composerTypingCorrectionProps;

  const composerProps = {
    value: draft,
    disabled: false,
    isSending,
    placeholder,
    onChange: onDraftChange,
    onSubmit,
    onCancel,
    ...composerAttachmentProps,
    ...composerPresentationFormatProps,
    ...composerResponseModeProps,
    ...composerContextProps,
    ...typingCorrectionProps,
  };

  if (isConversationEmpty) {
    return (
      <div className="mdc-chat-main mdc-chat-agent-conversation-surface">
        <section className="mdc-chat-empty-composer" aria-label={`Agente ${agent.name}`}>
          <div className="mdc-chat-empty-composer__column">
            <div className="mdc-chat-empty-composer__scroll">
              <ChatAgentHome
                agent={agent}
                onUseSuggestion={onIcebreaker}
                canManageAgent={canManageAgent}
                onManageAgent={onManageAgent}
                defaultIcebreakersHint={defaultIcebreakersHint}
              />
            </div>

            <ChatInput {...composerProps} variant="center" />
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="mdc-chat-main mdc-chat-agent-conversation-surface">
      <section className="mdc-chat-conversation" aria-label={`Conversa com ${agent.name}`}>
        <div className="mdc-chat-message-list-wrap">
          {messageList ?? (
            <ChatMessageList
              messages={messages}
              conversationKey={conversationKey ?? agent.id}
              isStreaming={isSending}
              isLoading={false}
              streamingStatus={streamingStatus}
              streamingAnswer={streamingAnswer}
              streamingToolCalls={streamingToolCalls}
              streamingActivityLog={streamingActivityLog}
            />
          )}
        </div>

        <div className="mdc-chat-composer-footer">
          {composerFooter}

          <ChatInput {...composerProps} variant="dock" />
        </div>
      </section>
    </div>
  );
}
