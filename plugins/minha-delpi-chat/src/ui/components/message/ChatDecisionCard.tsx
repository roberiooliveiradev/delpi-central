import type { ChatStoryBlock, ChatStoryPresentation } from "../../../data/api/chatTypes";

import "./ChatDecisionCard.css";

type ChatDecisionCardProps = {
  presentation: ChatStoryPresentation;
  onDrillDown?: (query: string) => void;
};

function statusLabel(status: string | null | undefined): string {
  switch (status) {
    case "ok":
      return "OK";
    case "attention":
      return "Atenção";
    case "critical":
      return "Crítico";
    default:
      return "Indefinido";
  }
}

function renderBlock(
  block: ChatStoryBlock,
  index: number,
  onDrillDown?: (query: string) => void,
) {
  const title = String(block.title ?? "").trim();
  const text = String(block.text ?? "").trim();
  const query = String(block.query ?? "").trim();

  if (!text) {
    return null;
  }

  if (block.kind === "verdict") {
    return (
      <div
        key={`verdict-${index}`}
        className={`mdc-decision-card__verdict mdc-decision-card__verdict--${block.status ?? "unknown"}`}
      >
        {title ? <h4 className="mdc-decision-card__block-title">{title}</h4> : null}
        <p className="mdc-decision-card__verdict-text">{text}</p>
        {block.status ? (
          <span className="mdc-decision-card__status-pill">{statusLabel(block.status)}</span>
        ) : null}
      </div>
    );
  }

  if (block.kind === "recommendation" && query && onDrillDown) {
    return (
      <div key={`recommendation-${index}`} className="mdc-decision-card__block">
        {title ? <h4 className="mdc-decision-card__block-title">{title}</h4> : null}
        <button
          type="button"
          className="mdc-decision-card__chip"
          onClick={() => onDrillDown(query)}
        >
          {text}
        </button>
      </div>
    );
  }

  if (block.kind === "hypothesis") {
    return (
      <div key={`hypothesis-${index}`} className="mdc-decision-card__block">
        {title ? <h4 className="mdc-decision-card__block-title">{title}</h4> : null}
        <p className="mdc-decision-card__block-text">
          {text}
          {block.confirmed === false ? (
            <span className="mdc-decision-card__hypothesis-note"> (hipótese não confirmada)</span>
          ) : null}
        </p>
      </div>
    );
  }

  return (
    <div key={`${block.kind}-${index}`} className="mdc-decision-card__block">
      {title ? <h4 className="mdc-decision-card__block-title">{title}</h4> : null}
      <p className="mdc-decision-card__block-text">{text}</p>
    </div>
  );
}

export function ChatDecisionCard({ presentation, onDrillDown }: ChatDecisionCardProps) {
  const title = String(presentation.title ?? "").trim();
  const blocks = Array.isArray(presentation.blocks) ? presentation.blocks : [];

  if (!blocks.length) {
    return null;
  }

  return (
    <section className="mdc-decision-card" aria-label={title || "Resumo da decisão"}>
      {title ? <h3 className="mdc-decision-card__title">{title}</h3> : null}
      <div className="mdc-decision-card__blocks">
        {blocks.map((block, index) => renderBlock(block, index, onDrillDown))}
      </div>
    </section>
  );
}
