import type { ChatDepthState, ChatPaginationState } from "../../../data/api/chatTypes";

import { ChatMarkdown } from "./ChatMarkdown";

type AssistantContentChromeProps = {
  insight?: string | null;
  recommendations?: Array<{ label: string; reason?: string; query: string }>;
  pagination?: ChatPaginationState | null;
  depth?: ChatDepthState | null;
  onNavigate?: (query: string) => void;
};

function CoverageNavigation({
  pagination,
  depth,
  onNavigate,
}: {
  pagination: ChatPaginationState | null;
  depth: ChatDepthState | null;
  onNavigate?: (query: string) => void;
}) {
  if (!onNavigate || (!pagination && !depth)) {
    return null;
  }

  const showPagination =
    pagination &&
    (pagination.hasPrevious || pagination.hasNext || (pagination.totalPages ?? 0) > 1);

  if (!showPagination && !depth?.canIncrease) {
    return null;
  }

  return (
    <div className="mdc-rich-presentation__navigation" role="navigation" aria-label="Navegação dos dados">
      {showPagination && pagination ? (
        <div className="mdc-rich-presentation__pagination">
          <button
            type="button"
            className="mdc-rich-presentation__nav-btn"
            disabled={!pagination.hasPrevious}
            onClick={() => onNavigate("página anterior")}
          >
            Anterior
          </button>
          <span className="mdc-rich-presentation__pagination-label">
            Página {pagination.page}
            {pagination.totalPages ? ` de ${pagination.totalPages}` : ""}
            {pagination.total !== undefined
              ? ` · ${pagination.total} registro(s)`
              : ""}
          </span>
          <button
            type="button"
            className="mdc-rich-presentation__nav-btn"
            disabled={!pagination.hasNext}
            onClick={() => onNavigate("próxima página")}
          >
            Próxima
          </button>
        </div>
      ) : null}

      {depth?.canIncrease ? (
        <button
          type="button"
          className="mdc-rich-presentation__nav-btn mdc-rich-presentation__nav-btn--secondary"
          onClick={() => onNavigate("aumente a profundidade para 99")}
        >
          Ampliar níveis
        </button>
      ) : null}
    </div>
  );
}

export function AssistantContentChrome({
  insight,
  recommendations = [],
  pagination = null,
  depth = null,
  onNavigate,
}: AssistantContentChromeProps) {
  return (
    <>
      {insight ? (
        <div
          className="mdc-rich-presentation__insight"
          role="note"
          title="Por que este formato"
        >
          <ChatMarkdown content={insight} />
        </div>
      ) : null}

      {recommendations.length > 0 ? (
        <div
          className="mdc-rich-presentation__recommendations"
          role="note"
          aria-label="Sugestões de visualização"
        >
          <span className="mdc-rich-presentation__recommendations-label">Sugestão:</span>
          <ul className="mdc-rich-presentation__recommendations-list">
            {recommendations.map((item) => (
              <li key={`${item.label}-${item.query}`}>
                <button
                  type="button"
                  className="mdc-rich-presentation__recommendation-link"
                  title={item.reason}
                  onClick={() => onNavigate?.(item.query)}
                  disabled={!onNavigate}
                >
                  {item.label}
                </button>
                {item.reason ? (
                  <span className="mdc-rich-presentation__recommendation-reason">
                    {" "}
                    — {item.reason}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <CoverageNavigation pagination={pagination} depth={depth} onNavigate={onNavigate} />
    </>
  );
}
