import { useMemo } from "react";

import { getFirstDisplayName } from "../../utils/authDisplayName";
import type {
  AssistantContextualHighlight,
  AssistantOnboardingPayload,
} from "../../data/api/chatTypes";
import { resolveStarterQueryForFeature } from "../chatShortcutPrompt";
import { splitWelcomeHeadline } from "../welcomeHeadline";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  displayName?: string | null;
  contextualHighlights?: AssistantContextualHighlight[];
  onboarding?: AssistantOnboardingPayload | null;
  catalogLoading?: boolean;
  catalogError?: boolean;
  selectedProfileId?: string | null;
  onSelectProfile?: (profileId: string) => void;
  onUseStarter?: (query: string, featureId?: string | null) => void;
  onStartTour?: () => void;
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
  contextualHighlights = [],
  onboarding,
  catalogLoading = false,
  catalogError = false,
  selectedProfileId,
  onSelectProfile,
  onUseStarter,
  onStartTour,
}: ChatEmptyStateProps) {
  const firstName = getFirstDisplayName(displayName);
  const greeting = useMemo(() => pickGreeting(firstName), [firstName]);
  const welcomeTitle = onboarding?.welcome?.title?.trim();
  const welcomeSubtitle = onboarding?.welcome?.subtitle?.trim();
  const starterCards = onboarding?.starterCards ?? [];
  const profiles = onboarding?.profiles ?? [];
  const activeProfileId = selectedProfileId ?? onboarding?.selectedProfileId ?? null;
  const headlineParts = useMemo(
    () => (welcomeTitle ? splitWelcomeHeadline(welcomeTitle) : null),
    [welcomeTitle],
  );
  const showOnboardingCards =
    !catalogLoading &&
    starterCards.length > 0 &&
    Boolean(onUseStarter);
  const showCatalogSkeleton = catalogLoading;
  const showCatalogError =
    !catalogLoading && catalogError && starterCards.length === 0;

  return (
    <section className="mdc-chat-empty-state" aria-label="Início da conversa">
      <div className="mdc-chat-empty-state__hero">
        <h2 className="mdc-chat-empty-state__headline">
          {headlineParts ? (
            <>
              <span className="mdc-chat-empty-state__headline-main">{headlineParts.lead}</span>
              {headlineParts.accent ? (
                <span className="mdc-chat-empty-state__headline-accent">{headlineParts.accent}</span>
              ) : null}
            </>
          ) : (
            <span className="mdc-chat-empty-state__headline-main">{greeting}</span>
          )}
        </h2>
        <p className="mdc-chat-empty-state__hint">
          {welcomeSubtitle ||
            "Escolha uma sugestão ou escreva do seu jeito. Aceito pequenos errinhos de digitação."}
        </p>
        {onStartTour ? (
          <button
            type="button"
            className="mdc-chat-empty-state__tour-link"
            onClick={onStartTour}
          >
            Ver tour rápido do chat
          </button>
        ) : null}
      </div>

      {showCatalogSkeleton ? (
        <div
          className="mdc-chat-empty-state__skeleton"
          aria-busy="true"
          aria-label="Carregando sugestões"
        >
          <div className="mdc-chat-empty-state__skeleton-profiles" />
          <div className="mdc-chat-empty-state__skeleton-cards" />
        </div>
      ) : null}

      {!catalogLoading && profiles.length > 0 && onSelectProfile ? (
        <div
          className="mdc-chat-empty-state__profiles"
          role="tablist"
          aria-label="Perfil de uso"
          data-tour="profiles"
        >
          {profiles.map((profile) => (
            <button
              key={profile.id}
              type="button"
              role="tab"
              aria-selected={profile.id === activeProfileId}
              className={
                profile.id === activeProfileId
                  ? "mdc-chat-empty-state__profile mdc-chat-empty-state__profile--active"
                  : "mdc-chat-empty-state__profile"
              }
              title={profile.subtitle}
              onClick={() => onSelectProfile(profile.id)}
            >
              {profile.label}
            </button>
          ))}
        </div>
      ) : null}

      {showCatalogError ? (
        <p className="mdc-chat-empty-state__catalog-error">
          Não foi possível carregar as sugestões. Use o campo abaixo ou tente recarregar a página.
        </p>
      ) : null}

      {showOnboardingCards ? (
        <div
          className="mdc-chat-empty-state__cards"
          role="group"
          aria-label="Opções para começar"
          data-tour="starter-cards"
        >
          {starterCards.map((card) => (
            <button
              key={card.id}
              type="button"
              className="mdc-chat-empty-state__card"
              onClick={() => onUseStarter(card.query, card.id)}
            >
              <strong>{card.label}</strong>
              {card.description ? <span>{card.description}</span> : null}
            </button>
          ))}
        </div>
      ) : null}

      {contextualHighlights.length > 0 ? (
        <div className="mdc-chat-empty-state__highlights" role="region" aria-label="Novidades do chat">
          <p className="mdc-chat-empty-state__highlights-label">Novidades</p>
          {contextualHighlights.slice(0, 2).map((highlight) => (
            <button
              key={highlight.featureId ?? highlight.title}
              type="button"
              className="mdc-chat-empty-state__highlight-chip"
              title={highlight.description}
              onClick={() => {
                const query = resolveStarterQueryForFeature(
                  highlight.exampleQuery,
                  highlight.featureId,
                );

                if (query) {
                  onUseStarter?.(query, highlight.featureId);
                }
              }}
            >
              <strong>{highlight.title}</strong>
              {highlight.description ? (
                <span>{highlight.description}</span>
              ) : null}
            </button>
          ))}
        </div>
      ) : null}

    </section>
  );
}
