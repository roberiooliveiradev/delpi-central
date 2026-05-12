import type { ChatSource } from "../../data/api/chatTypes";

import "./ChatSources.css";

type ChatSourcesProps = {
  sources?: ChatSource[];
};

function formatScore(score?: number): string {
  if (typeof score !== "number" || Number.isNaN(score)) {
    return "sem score";
  }

  return `${Math.round(score * 100)}%`;
}

function formatSourceLabel(source: ChatSource): string {
  const parts = [
    source.sourceType,
    source.sourceRef,
    typeof source.chunkIndex === "number" ? `chunk ${source.chunkIndex}` : null,
  ].filter(Boolean);

  return parts.join(" · ");
}

export function ChatSources({ sources }: ChatSourcesProps) {
  if (!sources?.length) {
    return null;
  }

  return (
    <section className="mdc-chat-sources" aria-label="Fontes da resposta">
      <details className="mdc-chat-sources-details">
        <summary>
          <span>Fontes consultadas</span>
          <strong>{sources.length}</strong>
        </summary>

        <div className="mdc-chat-sources-list">
          {sources.map((source, index) => (
            <article
              className="mdc-chat-source-card"
              key={`${source.id ?? source.documentId ?? index}-${source.chunkIndex ?? index}`}
            >
              <div className="mdc-chat-source-card__header">
                <strong>{source.title || "Fonte sem título"}</strong>
                <span>{formatScore(source.score)}</span>
              </div>

              <dl className="mdc-chat-source-card__meta">
                <div>
                  <dt>Origem</dt>
                  <dd>{formatSourceLabel(source) || "Não informada"}</dd>
                </div>

                {source.documentId ? (
                  <div>
                    <dt>Documento</dt>
                    <dd>{source.documentId}</dd>
                  </div>
                ) : null}
              </dl>
            </article>
          ))}
        </div>
      </details>
    </section>
  );
}
