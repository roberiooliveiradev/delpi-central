import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";

import type { ChatMessageBranch } from "../../data/api/chatTypes";

type ChatBranchNavigatorProps = {
  branch: ChatMessageBranch;
  disabled?: boolean;
  isLoading?: boolean;
  onSelectSibling: (anchorUserMessageId: string) => void;
};

export function ChatBranchNavigator({
  branch,
  disabled = false,
  isLoading = false,
  onSelectSibling,
}: ChatBranchNavigatorProps) {
  if (branch.total <= 1) {
    return null;
  }

  const currentIndex = Math.min(Math.max(branch.currentIndex, 1), branch.total);
  const siblingIndex = currentIndex - 1;

  function selectSibling(offset: number) {
    if (isLoading) {
      return;
    }

    const nextIndex = siblingIndex + offset;

    if (nextIndex < 0 || nextIndex >= branch.siblingIds.length) {
      return;
    }

    const nextId = branch.siblingIds[nextIndex];

    if (nextId) {
      onSelectSibling(nextId);
    }
  }

  const controlsDisabled = disabled || isLoading;

  return (
    <div
      className={`mdc-chat-branch-nav${isLoading ? " mdc-chat-branch-nav--loading" : ""}`}
      aria-label="Alternar variação da pergunta"
      aria-busy={isLoading}
    >
      <button
        type="button"
        className="mdc-chat-branch-nav__button"
        disabled={controlsDisabled || currentIndex <= 1}
        aria-label="Variação anterior"
        title="Variação anterior"
        onClick={() => selectSibling(-1)}
      >
        <ChevronLeft size={16} strokeWidth={2.25} aria-hidden="true" />
      </button>

      <span className="mdc-chat-branch-nav__label">
        {currentIndex}/{branch.total}
      </span>

      <button
        type="button"
        className="mdc-chat-branch-nav__button"
        disabled={controlsDisabled || currentIndex >= branch.total}
        aria-label="Próxima variação"
        title="Próxima variação"
        onClick={() => selectSibling(1)}
      >
        <ChevronRight size={16} strokeWidth={2.25} aria-hidden="true" />
      </button>

      {isLoading ? (
        <Loader2
          size={14}
          className="mdc-chat-branch-nav__spinner"
          aria-hidden="true"
        />
      ) : null}
    </div>
  );
}
