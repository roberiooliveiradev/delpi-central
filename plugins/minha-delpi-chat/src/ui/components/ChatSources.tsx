import type { ChatSource } from "../../data/api/chatTypes";

import "./ChatSources.css";

type ChatSourcesProps = {
  sources?: ChatSource[];
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

function resolveSourcesLabel(sources: ChatSource[]): string {
  const hasWebSources = sources.some(
    (source) => String(source.scope ?? "").trim().toLowerCase() === "web_search",
  );

  if (hasWebSources) {
    return sources.length === 1 ? "Fonte" : "Fontes";
  }

  return sources.length === 1 ? "Fonte de conhecimento" : "Fontes de conhecimento";
}

export function ChatSources({ sources }: ChatSourcesProps) {
  if (!sources?.length) {
    return null;
  }

  const label = resolveSourcesLabel(sources);

  return (
    <section className="mdc-chat-sources" aria-label="Fontes da resposta">
      <div className="mdc-chat-sources-badges">
        <span className="mdc-chat-sources-badges__label">{label}</span>
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
  );
}
