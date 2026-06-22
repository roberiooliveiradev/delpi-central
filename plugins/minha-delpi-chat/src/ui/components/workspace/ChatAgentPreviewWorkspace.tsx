import type { ChatAgent } from "../../../data/api/chatTypes";
import type { ChatAgentPreviewDraft } from "../../../data/api/chatTypes";
import { useAgentPreviewConversation } from "../../../state/hooks/useAgentPreviewConversation";
import { useChatComposerBindings } from "../../../state/hooks/useChatComposerBindings";
import { useChatShortcutPrompt } from "../../hooks/useChatShortcutPrompt";
import {
  hasUnresolvedShortcutPlaceholders,
  resolveStarterPromptOptions,
  starterRequiresShortcutModal,
} from "../../chatShortcutPrompt";
import {
  icebreakerRequiresShortcutModal,
  resolveIcebreakerPromptOptions,
  type AgentIcebreakerEntry,
} from "../../agentIcebreakers";
import { ChatAgentConversationSurface } from "./ChatAgentConversationSurface";

import "./ChatAgentPreviewWorkspace.css";

type ChatAgentPreviewWorkspaceProps = {
  agent: ChatAgent;
  defaultIcebreakersHint?: string | null;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  buildDraft: () => ChatAgentPreviewDraft;
  validateDraft?: () => string | null;
};

export function ChatAgentPreviewWorkspace({
  agent,
  defaultIcebreakersHint,
  getAccessToken,
  buildDraft,
  validateDraft,
}: ChatAgentPreviewWorkspaceProps) {
  const {
    messages,
    draft,
    setDraft,
    isSending,
    sendMessage,
    streamingAnswer,
    streamingToolCalls,
    streamingActivityLog,
    streamingStatus,
  } = useAgentPreviewConversation({
    agentId: agent.id,
    getAccessToken,
    buildDraft,
    validateDraft,
  });

  const composerBindings = useChatComposerBindings({
    sessionId: null,
    draft,
    onDraftChange: setDraft,
    getAccessToken,
    agents: [agent],
    pageAgentId: agent.id,
    contextAgentIds: [agent.id],
  });

  const { resolveShortcutQuery, shortcutPromptDialog } = useChatShortcutPrompt();

  const hasActiveConversation = messages.length > 0 || isSending;

  async function submitMessage(rawContent?: string) {
    const content = (rawContent ?? draft).trim();

    if (!content || isSending) {
      return;
    }

    if (!starterRequiresShortcutModal(content, {})) {
      await sendMessage(content);
      return;
    }

    const promptOptions = resolveStarterPromptOptions(content, {});
    const resolved = await resolveShortcutQuery(content, promptOptions);

    if (!resolved || hasUnresolvedShortcutPlaceholders(resolved)) {
      return;
    }

    await sendMessage(resolved);
  }

  async function handleIcebreaker(entry: AgentIcebreakerEntry) {
    const template = entry.template.trim();

    if (!icebreakerRequiresShortcutModal(entry)) {
      await sendMessage(template);
      return;
    }

    const promptOptions = resolveIcebreakerPromptOptions(entry);
    const resolved = await resolveShortcutQuery(template, promptOptions);

    if (!resolved || hasUnresolvedShortcutPlaceholders(resolved)) {
      return;
    }

    await sendMessage(resolved);
  }

  return (
    <>
      {shortcutPromptDialog}

      <div className="mdc-chat-agent-preview-workspace">
        <ChatAgentConversationSurface
          agent={agent}
          messages={messages}
          draft={draft}
          isSending={isSending}
          isConversationEmpty={!hasActiveConversation}
          composerBindings={composerBindings}
          onDraftChange={setDraft}
          onSubmit={() => void submitMessage()}
          onIcebreaker={(entry) => {
            void handleIcebreaker(entry);
          }}
          defaultIcebreakersHint={defaultIcebreakersHint}
          streamingStatus={streamingStatus ?? undefined}
          streamingAnswer={streamingAnswer}
          streamingToolCalls={streamingToolCalls}
          streamingActivityLog={streamingActivityLog}
        />
      </div>
    </>
  );
}
