import { useEffect, useRef, type ReactNode } from "react";
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";

type ChartSeriesViewportProps = {
  navigable: boolean;
  rangeLabel: string;
  page: number;
  pageCount: number;
  total: number;
  windowSize: number;
  offset: number;
  onStart: () => void;
  onPrevPage: () => void;
  onNextPage: () => void;
  onEnd: () => void;
  onShift: (delta: number) => void;
  children: ReactNode;
};

const WHEEL_STEP = 4;

export function ChartSeriesViewport({
  navigable,
  rangeLabel,
  page,
  pageCount,
  total,
  windowSize,
  offset,
  onStart,
  onPrevPage,
  onNextPage,
  onEnd,
  onShift,
  children,
}: ChartSeriesViewportProps) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const atStart = offset <= 0;
  const atEnd = offset >= Math.max(0, total - windowSize);

  useEffect(() => {
    if (!navigable) return undefined;

    const element = viewportRef.current;
    if (!element) return undefined;

    const handleWheel = (event: WheelEvent) => {
      const dominantDelta =
        Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
      if (dominantDelta === 0) return;

      event.preventDefault();
      const direction = dominantDelta > 0 ? 1 : -1;
      onShift(direction * WHEEL_STEP);
    };

    element.addEventListener("wheel", handleWheel, { passive: false });
    return () => element.removeEventListener("wheel", handleWheel);
  }, [navigable, onShift]);

  return (
    <div className="ds-chart-viewport">
      {navigable ? (
        <div className="ds-chart-nav" role="toolbar" aria-label="Navegação do gráfico">
          <div className="ds-chart-nav__actions">
            <button
              type="button"
              className="ds-ghost-btn ds-chart-nav__btn"
              onClick={onStart}
              disabled={atStart}
              aria-label="Início da série"
              title="Início"
            >
              <ChevronsLeft size={16} />
            </button>
            <button
              type="button"
              className="ds-ghost-btn ds-chart-nav__btn"
              onClick={onPrevPage}
              disabled={atStart}
              aria-label="Período anterior"
              title="Anterior"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              type="button"
              className="ds-ghost-btn ds-chart-nav__btn"
              onClick={onNextPage}
              disabled={atEnd}
              aria-label="Próximo período"
              title="Próximo"
            >
              <ChevronRight size={16} />
            </button>
            <button
              type="button"
              className="ds-ghost-btn ds-chart-nav__btn"
              onClick={onEnd}
              disabled={atEnd}
              aria-label="Fim da série"
              title="Fim"
            >
              <ChevronsRight size={16} />
            </button>
          </div>
          <p className="ds-chart-nav__meta">
            <span className="ds-chart-nav__range">{rangeLabel}</span>
            <span className="ds-chart-nav__pages">
              Página {page} de {pageCount} · {total} períodos · role o mouse no gráfico
            </span>
          </p>
        </div>
      ) : null}

      <div
        ref={viewportRef}
        className={navigable ? "ds-chart-viewport__canvas ds-chart-viewport__canvas--scrollable" : "ds-chart-viewport__canvas"}
        tabIndex={navigable ? 0 : undefined}
        onKeyDown={
          navigable
            ? (event) => {
                if (event.key === "ArrowLeft") {
                  event.preventDefault();
                  onShift(-WHEEL_STEP);
                }
                if (event.key === "ArrowRight") {
                  event.preventDefault();
                  onShift(WHEEL_STEP);
                }
                if (event.key === "Home") {
                  event.preventDefault();
                  onStart();
                }
                if (event.key === "End") {
                  event.preventDefault();
                  onEnd();
                }
              }
            : undefined
        }
      >
        {children}
      </div>
    </div>
  );
}
