import type { ChatSource } from "../../data/api/chatTypes";

type ChatSourcesProps = {
  sources?: ChatSource[];
};

export function ChatSources({ sources }: ChatSourcesProps) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="mdc-chat-sources" aria-label="Fontes consultadas">
      <strong>Fontes</strong>

      <ul>
        {sources.map((source, index) => (
          <li key={source.id ?? `${source.documentId}-${source.chunkIndex}-${index}`}>
            <span>{source.title || "Fonte sem título"}</span>
            {source.sourceRef ? <small>{source.sourceRef}</small> : null}
            {typeof source.score === "number" ? (
              <small>score {source.score.toFixed(2)}</small>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
