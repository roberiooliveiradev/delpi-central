import { getFirstDisplayName } from "../../utils/authDisplayName";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  displayName?: string | null;
};

export function ChatEmptyState({ displayName }: ChatEmptyStateProps) {
  const firstName = getFirstDisplayName(displayName);

  const greeting = firstName
    ? `Ei, ${firstName}. Tudo pronto para começar?`
    : "Tudo pronto para começar?";

  return (
    <section className="mdc-chat-empty-state" aria-label="Início da conversa">
      <div className="mdc-chat-empty-state__hero">
        <h2>{greeting}</h2>
      </div>
    </section>
  );
}
