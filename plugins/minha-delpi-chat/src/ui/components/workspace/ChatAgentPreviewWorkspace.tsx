import { useMemo, useState } from "react";

import type { ChatAgent, ChatMessage } from "../../../data/api/chatTypes";
import { formatComposerPlaceholderParts } from "../../../state/chatComposerContext";
import { useChatPresentationFormat } from "../../../state/hooks/useChatPresentationFormat";
import { useChatResponseMode } from "../../../state/hooks/useChatResponseMode";
import { useChatTypingCorrection } from "../../../state/hooks/useChatTypingCorrection";
import { getTypingCorrectionContent } from "../../../content/messageComposerContent";
import { useChatShortcutPrompt } from "../../hooks/useChatShortcutPrompt";
import {
  hasUnresolvedShortcutPlaceholders,
  resolveStarterPromptOptions,
  starterRequiresShortcutModal,
} from "../../chatShortcutPrompt";
import { ChatInput, type ChatInputAttachment } from "../composer/ChatInput";
import { ChatMessageList } from "../message/ChatMessageList";
import { ChatAgentHome } from "./ChatAgentHome";

import "./ChatAgentPreviewWorkspace.css";

type ChatAgentPreviewWorkspaceProps = {
  agent: ChatAgent;
  messages: ChatMessage[];
  draft: string;
  isSending: boolean;
  defaultIcebreakersHint?: string | null;
  onDraftChange: (value: string) => void;
  onSendMessage: (content: string) => Promise<void>;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function ChatAgentPreviewWorkspace({
  agent,
  messages,
  draft,
  isSending,
  defaultIcebreakersHint,
  onDraftChange,
  onSendMessage,
  getAccessToken,
}: ChatAgentPreviewWorkspaceProps) {
  const [composerAttachments, setComposerAttachments] = useState<ChatInputAttachment[]>([]);

  const {
    enabled: responseModesEnabled,
    modes: responseModes,
    responseMode,
    setResponseMode,
  } = useChatResponseMode({ getAccessToken });

  const {
    options: presentationFormatOptions,
    presentationFormat,
    setPresentationFormat,
  } = useChatPresentationFormat({
    sessionId: null,
    getAccessToken,
  });

  const typingCorrectionLabels = useMemo(() => getTypingCorrectionContent(), []);
  const {
    suggestion: typingSuggestion,
    dismissSuggestion: dismissTypingSuggestionState,
  } = useChatTypingCorrection({
    draft,
    sessionId: null,
    enabled: true,
    getAccessToken,
  });

  const { resolveShortcutQuery, shortcutPromptDialog } = useChatShortcutPrompt();

  const placeholder =
    formatComposerPlaceholderParts({
      agentNames: [agent.name],
    }) ?? "Pergunte alguma coisa";

  const hasActiveConversation = messages.length > 0 || isSending;
  const isConversationEmpty = !hasActiveConversation;

  async function submitMessage(rawContent?: string) {
    const content = (rawContent ?? draft).trim();

    if (!content || isSending) {
      return;
    }

    if (!starterRequiresShortcutModal(content, {})) {
      onDraftChange("");
      await onSendMessage(content);
      return;
    }

    const promptOptions = resolveStarterPromptOptions(content, {});
    const resolved = await resolveShortcutQuery(content, promptOptions);

    if (!resolved || hasUnresolvedShortcutPlaceholders(resolved)) {
      return;
    }

    onDraftChange("");
    await onSendMessage(resolved);
  }

  async function handleIcebreaker(template: string) {
    if (!starterRequiresShortcutModal(template, {})) {
      await onSendMessage(template);
      return;
    }

    const promptOptions = resolveStarterPromptOptions(template, {});
    const resolved = await resolveShortcutQuery(template, promptOptions);

    if (!resolved || hasUnresolvedShortcutPlaceholders(resolved)) {
      return;
    }

    await onSendMessage(resolved);
  }

  const composerProps = {
    value: draft,
    disabled: false,
    isSending,
    placeholder,
    agents: [agent],
    selectedAgentIds: [agent.id],
    attachments: composerAttachments,
    onAttachFiles: (files: File[]) => {
      setComposerAttachments((current) => [
        ...current,
        ...files.map((file) => ({
          id: `preview-attachment-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          name: file.name,
          size: file.size,
          type: file.type,
          file,
          status: "queued" as const,
        })),
      ]);
    },
    onRemoveAttachment: (attachmentId: string) => {
      setComposerAttachments((current) => current.filter((item) => item.id !== attachmentId));
    },
    onClearAttachments: () => setComposerAttachments([]),
    showResponseModeSelector: responseModesEnabled,
    responseModes,
    responseMode,
    onResponseModeChange: setResponseMode,
    showPresentationFormatSelector: true,
    presentationFormatOptions,
    presentationFormat,
    onPresentationFormatChange: setPresentationFormat,
    typingSuggestion,
    typingSuggestionLabels: typingCorrectionLabels,
    onAcceptTypingSuggestion: () => {
      if (!typingSuggestion) {
        return;
      }

      onDraftChange(typingSuggestion.corrected);
      dismissTypingSuggestionState();
    },
    onDismissTypingSuggestion: dismissTypingSuggestionState,
    onChange: onDraftChange,
    onSubmit: () => void submitMessage(),
    getAccessToken,
  };

  return (
    <div className="mdc-chat-agent-preview-workspace">
      {shortcutPromptDialog}

      {isConversationEmpty ? (
        <section className="mdc-chat-empty-composer" aria-label="Pré-visualização do agente">
          <div className="mdc-chat-empty-composer__column">
            <div className="mdc-chat-empty-composer__scroll">
              <ChatAgentHome
                agent={agent}
                defaultIcebreakersHint={defaultIcebreakersHint}
                onUseSuggestion={(query) => {
                  void handleIcebreaker(query);
                }}
              />
            </div>

            <ChatInput {...composerProps} variant="center" />
          </div>
        </section>
      ) : (
        <section className="mdc-chat-conversation" aria-label="Pré-visualização do agente">
          <div className="mdc-chat-message-list-wrap">
            <ChatMessageList
              messages={messages}
              conversationKey={agent.id}
              isStreaming={isSending}
              isLoading={false}
              streamingStatus={isSending ? "Gerando resposta..." : undefined}
            />
          </div>

          <div className="mdc-chat-composer-footer">
            <ChatInput {...composerProps} variant="dock" />
          </div>
        </section>
      )}
    </div>
  );
}
