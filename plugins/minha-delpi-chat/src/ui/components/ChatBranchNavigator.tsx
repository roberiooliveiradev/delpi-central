import { ChevronLeft, ChevronRight } from "lucide-react";

import type { ChatMessageBranch } from "../../data/api/chatTypes";

type ChatBranchNavigatorProps = {
  branch: ChatMessageBranch;
  disabled?: boolean;
  onSelectSibling: (anchorUserMessageId: string) => void;
};

export function ChatBranchNavigator({
  branch,
  disabled = false,
  onSelectSibling,
}: ChatBranchNavigatorProps) {
  if (branch.total <= 1) {
    return null;
  }

  const currentIndex = Math.min(Math.max(branch.currentIndex, 1), branch.total);
  const siblingIndex = currentIndex - 1;

  function selectSibling(offset: number) {
    const nextIndex = siblingIndex + offset;

    if (nextIndex < 0 || nextIndex >= branch.siblingIds.length) {
      return;
    }

    const nextId = branch.siblingIds[nextIndex];

    if (nextId) {
      onSelectSibling(nextId);
    }
  }

  return (
    <div className="mdc-chat-branch-nav" aria-label="Alternar variação da pergunta">
      <button
        type="button"
        className="mdc-chat-branch-nav__button"
        disabled={disabled || currentIndex <= 1}
        aria-label="Variação anterior"
        onClick={() => selectSibling(-1)}
      >
        <ChevronLeft size={14} aria-hidden="true" />
      </button>

      <span className="mdc-chat-branch-nav__label">
        {currentIndex}/{branch.total}
      </span>

      <button
        type="button"
        className="mdc-chat-branch-nav__button"
        disabled={disabled || currentIndex >= branch.total}
        aria-label="Próxima variação"
        onClick={() => selectSibling(1)}
      >
        <ChevronRight size={14} aria-hidden="true" />
      </button>
    </div>
  );
}
