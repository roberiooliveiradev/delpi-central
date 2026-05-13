import { Network } from "lucide-react";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  onUseSuggestion?: (value: string) => void;
};

export function ChatEmptyState({ onUseSuggestion }: ChatEmptyStateProps) {
  return (
    <section className="mdc-chat-empty-state" aria-label="Início da conversa">
      <div className="mdc-chat-empty-state__hero">
        <h2>Ei, Robério. Tudo pronto para começar?</h2>
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
