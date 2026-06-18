import { ExternalLink, Globe2, Search, Sparkles, X } from "lucide-react";
import { useMemo } from "react";

import type {
  ChatWebSearchResearch,
  ChatWebSearchResearchSite,
  ChatWebSearchResearchStep,
} from "../../../data/api/chatTypes";
import { ChatModal } from "../shared/modal/ChatModal";

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

function confidenceLabel(confidence?: string | null): string | null {
  if (confidence === "high") {
    return "alta confiança";
  }

  if (confidence === "medium") {
    return "confiança moderada";
  }

  if (confidence === "low") {
    return "baixa confiança";
  }

  return null;
}

function ResearchSiteBadge({ site }: { site: ChatWebSearchResearchSite }) {
  const label = site.hostname || site.title || "fonte";
  const official = site.isOfficial === true;

  return (
    <a
      className={`mdc-chat-web-research__site${official ? " mdc-chat-web-research__site--official" : ""}`}
      href={site.url}
      rel="noopener noreferrer"
      target="_blank"
      title={site.title || site.url}
    >
      <ExternalLink size={12} aria-hidden="true" />
      <span>{label}</span>
      {official ? <span className="mdc-chat-web-research__site-tag">oficial</span> : null}
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
  const confidenceText = confidenceLabel(research?.confidence);
  const warnings = research?.warnings ?? [];

  if (!open || !research) {
    return null;
  }

  return (
    <ChatModal
      open
      onClose={onClose}
      size="none"
      scrimLayout="drawer-end"
      panelClassName="mdc-chat-web-research-panel"
      ariaLabelledBy="mdc-chat-web-research-title"
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
            {research.integrationMode === "internal_product"
              ? " · produto + web"
              : research.integrationMode === "attachment_compare"
                ? " · anexo + web"
                : research.integrationMode === "source_compare"
                  ? " · comparar fontes"
                  : research.integrationMode === "technical_table"
                    ? " · tabela técnica"
                    : ""}
            {confidenceText ? ` · ${confidenceText}` : ""}
            {research.provider ? ` · ${research.provider}` : ""}
            {durationLabel ? ` · ${durationLabel}` : ""}
          </p>
        </div>

        <button
          type="button"
          className="mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--outlined mdc-chat-modal-icon-btn--sm"
          aria-label="Fechar atividade de pesquisa"
          onClick={onClose}
        >
          <X size={18} />
        </button>
      </header>

      <div className="mdc-chat-web-research-panel__body">
        {warnings.length > 0 ? (
          <section className="mdc-chat-web-research__warnings" role="note">
            <h3>Observações sobre as fontes</h3>
            <ul>
              {warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </section>
        ) : null}

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
    </ChatModal>
  );
}
