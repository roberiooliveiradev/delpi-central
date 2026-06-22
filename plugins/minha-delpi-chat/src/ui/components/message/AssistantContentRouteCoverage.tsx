import type { ChatDepthState, ChatPaginationState } from "../../../data/api/chatTypes";

type AssistantContentRouteCoverageProps = {
  message: string;
  kind?: string | null;
  pagination?: ChatPaginationState | null;
  depth?: ChatDepthState | null;
  onNavigate?: (query: string) => void;
};

export function AssistantContentRouteCoverage({
  message,
  kind = null,
  pagination = null,
  depth = null,
  onNavigate,
}: AssistantContentRouteCoverageProps) {
  const showPagination =
    pagination &&
    (pagination.hasPrevious || pagination.hasNext || (pagination.totalPages ?? 0) > 1);
  const showDepth = Boolean(depth?.canIncrease);
  const showNavigation = Boolean(onNavigate && (showPagination || showDepth));
  const noticeClassName =
    kind === "info"
      ? "mdc-rich-presentation__coverage-notice mdc-rich-presentation__coverage-notice--info"
      : "mdc-rich-presentation__coverage-notice";

  return (
    <div className="mdc-assistant-content__route-coverage">
      <div className={noticeClassName} role="status">
        {message}
      </div>

      {showNavigation ? (
        <div
          className="mdc-rich-presentation__navigation"
          role="navigation"
          aria-label="Navegação dos dados desta seção"
        >
          {showPagination && pagination ? (
            <div className="mdc-rich-presentation__pagination">
              <button
                type="button"
                className="mdc-rich-presentation__nav-btn"
                disabled={!pagination.hasPrevious}
                onClick={() => onNavigate?.("página anterior")}
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
                onClick={() => onNavigate?.("próxima página")}
              >
                Próxima
              </button>
            </div>
          ) : null}

          {showDepth && depth ? (
            <button
              type="button"
              className="mdc-rich-presentation__nav-btn mdc-rich-presentation__nav-btn--secondary"
              onClick={() => onNavigate?.("aumente a profundidade para 99")}
            >
              Ampliar níveis
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
