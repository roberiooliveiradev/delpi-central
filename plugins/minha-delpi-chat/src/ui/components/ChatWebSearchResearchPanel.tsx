import { ExternalLink, Globe2, Search, Sparkles, X } from "lucide-react";
import { useMemo } from "react";

import type {
  ChatWebSearchResearch,
  ChatWebSearchResearchSite,
  ChatWebSearchResearchStep,
} from "../../data/api/chatTypes";
import { ModalPortal } from "./ModalPortal";

import "./ChatWebSearchResearchPanel.css";

type ChatWebSearchResearchPanelProps = {
  open: boolean;
  research: ChatWebSearchResearch | null;
  onClose: () => void;
};

function formatDuration(durationMs?: number): string | null {
  if (typeof durationMs !== "number" || Number.isNaN(durationMs) || durationMs <= 0) {
    return null;
  }

  const seconds = Math.max(1, Math.round(durationMs / 1000));

  return `${seconds}s`;
}

function resolveStepIcon(step: ChatWebSearchResearchStep) {
  if (step.type === "synthesis") {
    return Sparkles;
  }

  if (step.type === "organize") {
    return Globe2;
  }

  return Search;
}

function ResearchSiteBadge({ site }: { site: ChatWebSearchResearchSite }) {
  const label = site.hostname || site.title || "fonte";

  return (
    <a
      className="mdc-chat-web-research__site"
      href={site.url}
      rel="noopener noreferrer"
      target="_blank"
      title={site.title || site.url}
    >
      <ExternalLink size={12} aria-hidden="true" />
      <span>{label}</span>
    </a>
  );
}

export function ChatWebSearchResearchPanel({
  open,
  research,
  onClose,
}: ChatWebSearchResearchPanelProps) {
  const steps = useMemo(() => research?.steps ?? [], [research?.steps]);
  const allSites = useMemo(() => research?.sites ?? [], [research?.sites]);
  const durationLabel = formatDuration(research?.durationMs);
  const sourceCount = research?.sourceCount ?? allSites.length;

  if (!open || !research) {
    return null;
  }

  return (
    <ModalPortal>
      <div className="mdc-chat-web-research-backdrop" onClick={onClose}>
        <aside
          className="mdc-chat-web-research-panel"
          role="dialog"
          aria-modal="true"
          aria-labelledby="mdc-chat-web-research-title"
          onClick={(event) => event.stopPropagation()}
        >
          <header className="mdc-chat-web-research-panel__header">
            <div>
              <p className="mdc-chat-web-research-panel__eyebrow">Atividade</p>
              <h2 id="mdc-chat-web-research-title">Pesquisa web</h2>
              <p className="mdc-chat-web-research-panel__meta">
                {sourceCount === 1 ? "1 fonte" : `${sourceCount} fontes`}
                {research.searchMode === "deep"
                  ? " · pesquisa profunda"
                  : research.searchMode === "quick"
                    ? " · pesquisa rápida"
                    : ""}
                {research.preferOfficial ? " · fontes oficiais" : ""}
                {research.provider ? ` · ${research.provider}` : ""}
                {durationLabel ? ` · ${durationLabel}` : ""}
              </p>
            </div>

            <button
              type="button"
              className="mdc-chat-web-research-panel__close"
              aria-label="Fechar atividade de pesquisa"
              onClick={onClose}
            >
              <X size={18} />
            </button>
          </header>

          <div className="mdc-chat-web-research-panel__body">
            <ol className="mdc-chat-web-research__steps">
              {steps.map((step) => {
                const Icon = resolveStepIcon(step);
                const sites = step.sites ?? [];

                return (
                  <li key={step.id} className="mdc-chat-web-research__step">
                    <div className="mdc-chat-web-research__step-head">
                      <span className="mdc-chat-web-research__step-icon" aria-hidden="true">
                        <Icon size={14} />
                      </span>
                      <div>
                        <p className="mdc-chat-web-research__step-message">{step.message}</p>
                        {step.query && step.type === "search" ? (
                          <p className="mdc-chat-web-research__step-query">{step.query}</p>
                        ) : null}
                      </div>
                    </div>

                    {sites.length > 0 ? (
                      <div className="mdc-chat-web-research__sites">
                        {sites.slice(0, 8).map((site) => (
                          <ResearchSiteBadge key={site.url} site={site} />
                        ))}
                        {sites.length > 8 ? (
                          <span className="mdc-chat-web-research__sites-more">
                            Mais {sites.length - 8}
                          </span>
                        ) : null}
                      </div>
                    ) : null}
                  </li>
                );
              })}
            </ol>

            {allSites.length > 0 ? (
              <section className="mdc-chat-web-research__all-sources">
                <h3>Todas as fontes consultadas</h3>
                <ul>
                  {allSites.map((site) => (
                    <li key={site.url}>
                      <a href={site.url} rel="noopener noreferrer" target="_blank">
                        <strong>{site.hostname}</strong>
                        <span>{site.title || site.url}</span>
                      </a>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
          </div>

          <footer className="mdc-chat-web-research-panel__footer">
            {durationLabel ? <span>Pesquisou por {durationLabel}</span> : null}
            <span>Pronto</span>
          </footer>
        </aside>
      </div>
    </ModalPortal>
  );
}
