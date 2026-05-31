import { useState } from "react";

import type {
  ChatSource,
  ChatWebSearchResearch,
} from "../../data/api/chatTypes";

import { ChatWebSearchResearchPanel } from "./ChatWebSearchResearchPanel";

import "./ChatSources.css";

type ChatSourcesProps = {
  sources?: ChatSource[];
  webSearchResearch?: ChatWebSearchResearch | null;
};

function resolveSourceTitle(source: ChatSource): string {
  const title = source.title?.trim();

  if (title) {
    return title;
  }

  const sourceRef = source.sourceRef?.trim();
  if (sourceRef) {
    return sourceRef;
  }

  return "Fonte sem título";
}

function formatQualityHint(source: ChatSource): string | null {
  const quality =
    typeof source.qualityScore === "number" && !Number.isNaN(source.qualityScore)
      ? Math.round(source.qualityScore * 100)
      : typeof source.score === "number" && !Number.isNaN(source.score)
        ? Math.round(source.score * 100)
        : null;

  if (quality === null) {
    return null;
  }

  return `${quality}%`;
}

function formatBadgeTitle(source: ChatSource): string {
  const label = resolveSourceTitle(source);
  const quality = formatQualityHint(source);

  return quality ? `${label} · confiança ${quality}` : label;
}

function resolveHostname(source: ChatSource): string {
  const href = resolveSourceHref(source);

  if (!href) {
    return resolveSourceTitle(source);
  }

  try {
    return new URL(href).hostname.replace(/^www\./, "");
  } catch {
    return resolveSourceTitle(source);
  }
}

function resolveSourceHref(source: ChatSource): string | null {
  const sourceRef = source.sourceRef?.trim();

  if (!sourceRef) {
    return null;
  }

  if (/^https?:\/\//i.test(sourceRef)) {
    return sourceRef;
  }

  return null;
}

function hasWebSearchSources(sources: ChatSource[]): boolean {
  return sources.some(
    (source) => String(source.scope ?? "").trim().toLowerCase() === "web_search",
  );
}

function resolveSourcesLabel(sources: ChatSource[]): string {
  if (hasWebSearchSources(sources)) {
    return sources.length === 1 ? "Fonte" : "Fontes";
  }

  return sources.length === 1 ? "Fonte de conhecimento" : "Fontes de conhecimento";
}

export function ChatSources({ sources, webSearchResearch }: ChatSourcesProps) {
  const [researchOpen, setResearchOpen] = useState(false);

  if (!sources?.length) {
    return null;
  }

  const label = resolveSourcesLabel(sources);
  const isWebSearch = hasWebSearchSources(sources);
  const sourceCount = webSearchResearch?.sourceCount ?? sources.length;
  const canOpenResearch = Boolean(isWebSearch && webSearchResearch);
  const showSourceCards = isWebSearch && sources.length >= 2;

  return (
    <>
      <section className="mdc-chat-sources" aria-label="Fontes da resposta">
        {showSourceCards ? (
          <ul className="mdc-chat-sources-cards" aria-label="Cards de fontes da pesquisa web">
            {sources.slice(0, 6).map((source, index) => {
              const href = resolveSourceHref(source);
              const hostname = resolveHostname(source);
              const title = resolveSourceTitle(source);
              const official = source.isOfficial === true;
              const quality = formatQualityHint(source);

              return (
                <li key={`${source.id ?? source.sourceRef ?? index}`}>
                  {href ? (
                    <a
                      className={`mdc-chat-sources-card${official ? " mdc-chat-sources-card--official" : ""}`}
                      href={href}
                      rel="noopener noreferrer"
                      target="_blank"
                      title={formatBadgeTitle(source)}
                    >
                      <span className="mdc-chat-sources-card__host">{hostname}</span>
                      <span className="mdc-chat-sources-card__title">{title}</span>
                      {official || quality ? (
                        <span className="mdc-chat-sources-card__meta">
                          {official ? "Oficial" : ""}
                          {official && quality ? " · " : ""}
                          {quality ? `confiança ${quality}` : ""}
                        </span>
                      ) : null}
                    </a>
                  ) : (
                    <span className="mdc-chat-sources-card" title={formatBadgeTitle(source)}>
                      <span className="mdc-chat-sources-card__host">{hostname}</span>
                      <span className="mdc-chat-sources-card__title">{title}</span>
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        ) : null}

        <div className="mdc-chat-sources-badges">
          {canOpenResearch ? (
            <button
              type="button"
              className="mdc-chat-sources__research-trigger"
              aria-haspopup="dialog"
              aria-expanded={researchOpen}
              onClick={() => setResearchOpen(true)}
            >
              {label} · {sourceCount}
            </button>
          ) : (
            <span className="mdc-chat-sources-badges__label">{label}</span>
          )}

          <ul className="mdc-chat-sources-badges__list">
            {sources.map((source, index) => {
              const href = resolveSourceHref(source);
              const badgeTitle = formatBadgeTitle(source);
              const badgeLabel = resolveSourceTitle(source);

              const official = source.isOfficial === true;

              return (
                <li key={`${source.id ?? source.documentId ?? index}-${source.chunkIndex ?? index}`}>
                  {href ? (
                    <a
                      className={`mdc-chat-source-badge mdc-chat-source-badge--link${official ? " mdc-chat-source-badge--official" : ""}`}
                      href={href}
                      rel="noopener noreferrer"
                      target="_blank"
                      title={badgeTitle}
                    >
                      {badgeLabel}
                      {official ? (
                        <span className="mdc-chat-source-badge__tag">oficial</span>
                      ) : null}
                    </a>
                  ) : (
                    <span
                      className={`mdc-chat-source-badge${official ? " mdc-chat-source-badge--official" : ""}`}
                      title={badgeTitle}
                    >
                      {badgeLabel}
                      {official ? (
                        <span className="mdc-chat-source-badge__tag">oficial</span>
                      ) : null}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      </section>

      <ChatWebSearchResearchPanel
        open={researchOpen}
        research={webSearchResearch ?? null}
        onClose={() => setResearchOpen(false)}
      />
    </>
  );
}
