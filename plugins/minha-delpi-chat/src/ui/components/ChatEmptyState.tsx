import { useMemo } from "react";

import { getFirstDisplayName } from "../../utils/authDisplayName";
import { CHAT_HOME_STARTERS, type ChatHomeStarter } from "../chatHomeStarters";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  displayName?: string | null;
  starters?: ChatHomeStarter[];
  onUseStarter?: (query: string) => void;
};

const GREETINGS_WITH_NAME = [
  (name: string) => `Ei, ${name}. O que vamos resolver hoje?`,
  (name: string) => `Olá, ${name}. Pode perguntar do seu jeito.`,
  (name: string) => `Oi, ${name}. Tudo pronto por aqui.`,
];

const GREETINGS_ANONYMOUS = [
  "O que vamos resolver hoje?",
  "Pode perguntar do seu jeito.",
  "Tudo pronto por aqui. Como posso ajudar?",
];

function pickGreeting(firstName: string | null): string {
  const daySeed = new Date().toISOString().slice(0, 10);

  if (firstName) {
    const index =
      Math.abs(daySeed.split("").reduce((acc, ch) => acc + ch.charCodeAt(0), 0)) %
      GREETINGS_WITH_NAME.length;

    return GREETINGS_WITH_NAME[index](firstName);
  }

  const index =
    Math.abs(daySeed.split("").reduce((acc, ch) => acc + ch.charCodeAt(0), 0) + 7) %
    GREETINGS_ANONYMOUS.length;

  return GREETINGS_ANONYMOUS[index];
}

export function ChatEmptyState({
  displayName,
  starters = CHAT_HOME_STARTERS,
  onUseStarter,
}: ChatEmptyStateProps) {
  const firstName = getFirstDisplayName(displayName);
  const greeting = useMemo(() => pickGreeting(firstName), [firstName]);
  const showStarters = Boolean(onUseStarter) && starters.length > 0;

  return (
    <section className="mdc-chat-empty-state" aria-label="Início da conversa">
      <div className="mdc-chat-empty-state__hero">
        <h2>{greeting}</h2>
        <p className="mdc-chat-empty-state__hint">
          Escolha uma sugestão ou escreva do seu jeito. Aceito pequenos errinhos de digitação.
        </p>
      </div>

      {showStarters ? (
        <div className="mdc-chat-empty-state__starters" role="group" aria-label="Sugestões">
          {starters.map((starter) => (
            <button
              key={starter.query}
              type="button"
              className="mdc-chat-empty-state__chip"
              onClick={() => onUseStarter?.(starter.query)}
            >
              {starter.label}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
