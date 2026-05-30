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

function formatBadgeTitle(source: ChatSource): string {
  const label = resolveSourceTitle(source);
  const score =
    typeof source.score === "number" && !Number.isNaN(source.score)
      ? ` · relevância ${Math.round(source.score * 100)}%`
      : "";

  return `${label}${score}`;
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

  return (
    <>
      <section className="mdc-chat-sources" aria-label="Fontes da resposta">
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

              return (
                <li key={`${source.id ?? source.documentId ?? index}-${source.chunkIndex ?? index}`}>
                  {href ? (
                    <a
                      className="mdc-chat-source-badge mdc-chat-source-badge--link"
                      href={href}
                      rel="noopener noreferrer"
                      target="_blank"
                      title={badgeTitle}
                    >
                      {badgeLabel}
                    </a>
                  ) : (
                    <span className="mdc-chat-source-badge" title={badgeTitle}>
                      {badgeLabel}
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
