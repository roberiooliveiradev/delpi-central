import { Bot, Network } from "lucide-react";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  activeAgentName?: string | null;
  onUseSuggestion?: (value: string) => void;
};

export function ChatEmptyState({
  activeAgentName,
  onUseSuggestion,
}: ChatEmptyStateProps) {
  return (
    <section className="mdc-chat-empty-state" aria-label="Início da conversa">
      <div className="mdc-chat-empty-state__hero">
        <h2>Ei, Robério. Tudo pronto para começar?</h2>

        {activeAgentName ? (
          <p className="mdc-chat-empty-state__context">
            <Bot size={16} aria-hidden="true" />
            <span>Usando agente: {activeAgentName}</span>
          </p>
        ) : null}
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
