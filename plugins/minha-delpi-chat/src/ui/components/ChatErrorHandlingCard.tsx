import type { ChatFollowUpSuggestion, ChatMessageMetadata } from "../../data/api/chatTypes";
import { ChatFollowUpChips } from "./ChatFollowUpChips";

import "./ChatErrorHandlingCard.css";

type ChatErrorHandlingCardProps = {
  metadata: ChatMessageMetadata;
  onUseSuggestion?: (query: string) => void;
};

export function ChatErrorHandlingCard({
  metadata,
  onUseSuggestion,
}: ChatErrorHandlingCardProps) {
  const handling = metadata.errorHandling;

  if (!handling?.type) {
    return null;
  }

  const suggestions =
    (metadata.errorRecoveryFollowUpSuggestions as ChatFollowUpSuggestion[] | undefined) ??
    [];

  return (
    <section className="mdc-chat-error-handling" aria-label="Orientação após erro ou vazio">
      {handling.title ? (
        <h4 className="mdc-chat-error-handling__title">{handling.title}</h4>
      ) : null}

      {handling.userMessage ? (
        <p className="mdc-chat-error-handling__message">{handling.userMessage}</p>
      ) : null}

      {handling.reasons?.length ? (
        <div className="mdc-chat-error-handling__reasons">
          <p className="mdc-chat-error-handling__label">Possíveis motivos:</p>
          <ul>
            {handling.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {handling.apiFailed && handling.affirmsNonExistence === false ? (
        <p className="mdc-chat-error-handling__note">
          A consulta não foi concluída — não afirmo que o dado não existe, apenas que não foi
          possível confirmar agora.
        </p>
      ) : null}

      <ChatFollowUpChips
        suggestions={suggestions}
        onUseSuggestion={onUseSuggestion}
        groupLabel="Recuperar consulta"
        ariaLabel="Ações sugeridas após erro ou resultado vazio"
      />
    </section>
  );
}
