import { Network } from "lucide-react";

import { getFirstDisplayName } from "../../utils/authDisplayName";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  displayName?: string | null;
  onUseSuggestion?: (value: string) => void;
};

export function ChatEmptyState({
  displayName,
  onUseSuggestion,
}: ChatEmptyStateProps) {
  const firstName = getFirstDisplayName(displayName);

  const greeting = firstName
    ? `Ei, ${firstName}. Tudo pronto para começar?`
    : "Tudo pronto para começar?";

  return (
    <section className="mdc-chat-empty-state" aria-label="Início da conversa">
      <div className="mdc-chat-empty-state__hero">
        <h2>{greeting}</h2>
      </div>

      <button
        type="button"
        className="mdc-chat-empty-state__knowledge-pill"
        onClick={() => onUseSuggestion?.("Use o conhecimento da empresa para responder.")}
      >
        <Network size={17} aria-hidden="true" />
        <span>Conhecimento da empresa</span>
      </button>
    </section>
  );
}
