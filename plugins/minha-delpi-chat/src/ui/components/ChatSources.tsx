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

export function ChatSources({ sources }: ChatSourcesProps) {
  if (!sources?.length) {
    return null;
  }

  const label =
    sources.length === 1 ? "Fonte de conhecimento" : "Fontes de conhecimento";

  return (
    <section className="mdc-chat-sources" aria-label="Fontes da resposta">
      <div className="mdc-chat-sources-badges">
        <span className="mdc-chat-sources-badges__label">{label}</span>
        <ul className="mdc-chat-sources-badges__list">
          {sources.map((source, index) => (
            <li key={`${source.id ?? source.documentId ?? index}-${source.chunkIndex ?? index}`}>
              <span className="mdc-chat-source-badge" title={formatBadgeTitle(source)}>
                {resolveSourceTitle(source)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
