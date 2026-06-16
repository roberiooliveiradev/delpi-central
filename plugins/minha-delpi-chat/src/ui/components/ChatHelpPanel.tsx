import { CircleHelp, Search, X } from "lucide-react";
import { useMemo } from "react";

import type {
  AssistantCatalogFeature,
  AssistantCatalogResponse,
} from "../../data/api/chatTypes";
import {
  resolveStarterQueryForFeature,
  type StarterInvokeContext,
} from "../chatShortcutPrompt";
import { ChatModal } from "./shared/modal/ChatModal";

import "./ChatHelpPanel.css";

type ChatHelpPanelProps = {
  open: boolean;
  catalog: AssistantCatalogResponse | null;
  loading: boolean;
  error: string | null;
  searchQuery: string;
  onSearchQueryChange: (value: string) => void;
  onClose: () => void;
  onTryPrompt: (query: string, context?: StarterInvokeContext) => void;
  /** Inicia o tour guiado (home vazia, passos disponíveis). */
  onStartTour?: () => void;
};

function resolveAvailabilityLabel(
  feature: AssistantCatalogFeature,
  catalog: AssistantCatalogResponse | null,
): { text: string; tone: "ok" | "warn" | "muted" } {
  if (!catalog) {
    return { text: "", tone: "muted" };
  }

  const id = feature.id;
  const buckets = catalog.availability;

  if (buckets.availableNow.some((item) => item.id === id)) {
    return { text: "Disponível agora", tone: "ok" };
  }

  if (buckets.disabled.some((item) => item.id === id)) {
    return { text: "Desligado neste ambiente", tone: "warn" };
  }

  if (buckets.requiresProfilePermission?.some((item) => item.id === id)) {
    return { text: "Seu perfil não tem permissão", tone: "warn" };
  }

  if (buckets.requiresPermission.some((item) => item.id === id)) {
    return { text: "Agente sem API habilitada", tone: "warn" };
  }

  if (buckets.requiresAgent.some((item) => item.id === id) || feature.requiresAgent) {
    return { text: "Escolha um agente com API", tone: "warn" };
  }

  return { text: "Disponível", tone: "ok" };
}

function FeatureCard({
  feature,
  catalog,
  onTryPrompt,
}: {
  feature: AssistantCatalogFeature;
  catalog: AssistantCatalogResponse | null;
  onTryPrompt: (query: string, context?: StarterInvokeContext) => void;
}) {
  const badge = resolveAvailabilityLabel(feature, catalog);
  const examples = (feature.examples ?? []).slice(0, 3);

  return (
    <article className="mdc-chat-help-panel__card">
      <h3>{feature.title}</h3>
      {badge.text ? (
        <em className={`mdc-chat-help-panel__badge mdc-chat-help-panel__badge--${badge.tone}`}>
          {badge.text}
        </em>
      ) : null}
      {feature.summary ? <p>{feature.summary}</p> : null}
      {examples.length > 0 ? (
        <div className="mdc-chat-help-panel__examples">
          {examples.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => {
                const query = resolveStarterQueryForFeature(example, {
                  featureId: feature.id,
                  starterId: feature.id,
                });

                if (query) {
                  onTryPrompt(query, { featureId: feature.id, starterId: feature.id });
                }
              }}
            >
              {example}
            </button>
          ))}
        </div>
      ) : null}
    </article>
  );
}

export function ChatHelpPanel({
  open,
  catalog,
  loading,
  error,
  searchQuery,
  onSearchQueryChange,
  onClose,
  onTryPrompt,
  onStartTour,
}: ChatHelpPanelProps) {
  const sections = useMemo(() => {
    if (!catalog) {
      return [];
    }

    if (catalog.categories.length > 0) {
      return catalog.categories;
    }

    return [
      {
        id: "all",
        label: "Funcionalidades",
        features: catalog.features,
      },
    ];
  }, [catalog]);

  const profileHint =
    catalog?.userContext && !catalog.userContext.canUseTools
      ? "Seu perfil não inclui uso de consultas ERP (tools). "
      : "";

  const agentHint = catalog?.agentName
    ? `${profileHint}Contexto: agente ${catalog.agentName}`
    : catalog?.agentId
      ? `${profileHint}Contexto: agente selecionado`
      : `${profileHint}Sem agente — algumas consultas pedem escolher um agente.`;

  return (
    <ChatModal
      open={open}
      onClose={onClose}
      size="none"
      scrimLayout="drawer-end"
      ariaLabelledBy="mdc-chat-help-title"
      panelClassName="mdc-chat-help-panel"
    >
      <header className="mdc-chat-help-panel__header">
        <div>
          <h2 id="mdc-chat-help-title" className="mdc-chat-help-panel__title">
            <CircleHelp size={18} aria-hidden="true" />
            <span>Ajuda do chat</span>
          </h2>
          <p>{agentHint}</p>
        </div>
        <button
          type="button"
          className="mdc-chat-help-panel__close"
          aria-label="Fechar ajuda"
          onClick={onClose}
        >
          <X size={18} aria-hidden="true" />
        </button>
      </header>

      <div className="mdc-chat-help-panel__search">
        <div className="mdc-chat-help-panel__search-wrap">
          <Search size={16} aria-hidden="true" />
          <input
            type="search"
            value={searchQuery}
            placeholder="Buscar funcionalidade (ex.: estoque, gráfico)"
            aria-label="Buscar na ajuda"
            onChange={(event) => onSearchQueryChange(event.target.value)}
          />
        </div>
      </div>

      {onStartTour ? (
        <div className="mdc-chat-help-panel__tour">
          <button type="button" className="mdc-chat-help-panel__tour-link" onClick={onStartTour}>
            Ver tour rápido do chat
          </button>
        </div>
      ) : null}

      <div className="mdc-chat-help-panel__body">
        {catalog?.contextualHighlights?.length && !searchQuery.trim() ? (
          <section className="mdc-chat-help-panel__highlights" aria-label="Novidades">
            <h3 className="mdc-chat-help-panel__section-title">
              Novidades
              {catalog.releaseVersion ? ` · ${catalog.releaseVersion}` : ""}
            </h3>
            {catalog.contextualHighlights.map((highlight) => (
              <article key={highlight.featureId ?? highlight.title} className="mdc-chat-help-panel__highlight-card">
                <h4>{highlight.title}</h4>
                {highlight.description ? <p>{highlight.description}</p> : null}
                {resolveStarterQueryForFeature(highlight.exampleQuery, {
                  featureId: highlight.featureId,
                }) ? (
                  <button
                    type="button"
                    onClick={() => {
                      const query = resolveStarterQueryForFeature(highlight.exampleQuery, {
                        featureId: highlight.featureId,
                      });

                      if (query) {
                        onTryPrompt(query, { featureId: highlight.featureId });
                      }
                    }}
                  >
                    Experimentar
                  </button>
                ) : null}
              </article>
            ))}
          </section>
        ) : null}

        {catalog?.quickPrompts?.length ? (
          <div className="mdc-chat-help-panel__quick">
            {catalog.quickPrompts.map((prompt) => (
              <button
                key={prompt.id}
                type="button"
                onClick={() =>
                  onTryPrompt(prompt.query, { starterId: prompt.id ?? undefined })
                }
              >
                {prompt.label}
              </button>
            ))}
          </div>
        ) : null}

        {loading ? (
          <p className="mdc-chat-help-panel__status">Carregando catálogo…</p>
        ) : null}

        {error ? (
          <p className="mdc-chat-help-panel__status mdc-chat-help-panel__status--error">
            {error}
          </p>
        ) : null}

        {!loading && !error
          ? sections.map((section) => (
              <section key={section.id}>
                <h3 className="mdc-chat-help-panel__section-title">{section.label}</h3>
                {section.features.map((feature) => (
                  <FeatureCard
                    key={feature.id}
                    feature={feature}
                    catalog={catalog}
                    onTryPrompt={onTryPrompt}
                  />
                ))}
              </section>
            ))
          : null}

        {catalog?.releaseNotesPreview && !searchQuery.trim() ? (
          <div className="mdc-chat-help-panel__release">{catalog.releaseNotesPreview}</div>
        ) : null}
      </div>
    </ChatModal>
  );
}
