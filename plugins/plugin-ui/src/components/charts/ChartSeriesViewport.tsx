import { useEffect, useRef, type ReactNode } from "react";
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { ghostBtnBemClasses } from "../../utils/ghostBtnBem";

export type ChartSeriesViewportLabels = {
  toolbarAria: string;
  start: string;
  prev: string;
  next: string;
  end: string;
  pages: (page: number, pageCount: number, total: number) => string;
};

const DEFAULT_LABELS: ChartSeriesViewportLabels = {
  toolbarAria: "Navegação do gráfico",
  start: "Início da série",
  prev: "Período anterior",
  next: "Próximo período",
  end: "Fim da série",
  pages: (page, pageCount, total) =>
    `Página ${page} de ${pageCount} · ${total} períodos · role o mouse no gráfico`,
};

export type ChartSeriesViewportClassNames = {
  root: string;
  nav: string;
  actions: string;
  button: string;
  meta: string;
  range: string;
  pages: string;
  canvas: string;
  canvasScrollable: string;
};

export function chartSeriesViewportBemClasses(prefix: string): ChartSeriesViewportClassNames {
  const ui = "delpi-ui-chart-series-viewport";
  return {
    root: delpiUiClass(`${prefix}-chart-viewport`, ui),
    nav: delpiUiClass(`${prefix}-chart-nav`, `${ui}__nav`),
    actions: delpiUiClass(`${prefix}-chart-nav__actions`, `${ui}__actions`),
    button: delpiUiClass(
      `${prefix}-chart-nav__btn`,
      `${ui}__btn`,
    ),
    meta: delpiUiClass(`${prefix}-chart-nav__meta`, `${ui}__meta`),
    range: delpiUiClass(`${prefix}-chart-nav__range`, `${ui}__range`),
    pages: delpiUiClass(`${prefix}-chart-nav__pages`, `${ui}__pages`),
    canvas: delpiUiClass(`${prefix}-chart-viewport__canvas`, `${ui}__canvas`),
    canvasScrollable: delpiUiClass(
      `${prefix}-chart-viewport__canvas--scrollable`,
      `${ui}__canvas--scrollable`,
    ),
  };
}

export type ChartSeriesViewportProps = {
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
  /** Prefixo BEM dual-class (ex.: `ds`, `kz`). Default: `ds`. */
  prefix?: string;
  classNames?: Partial<ChartSeriesViewportClassNames>;
  labels?: Partial<ChartSeriesViewportLabels>;
  /** Classes do botão ghost (dual-class). Default: ghost do mesmo prefix. */
  ghostButtonClassName?: string;
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
  prefix = "ds",
  classNames: classNamesOverride,
  labels: labelsOverride,
  ghostButtonClassName,
}: ChartSeriesViewportProps) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const atStart = offset <= 0;
  const atEnd = offset >= Math.max(0, total - windowSize);
  const base = chartSeriesViewportBemClasses(prefix);
  const cn: ChartSeriesViewportClassNames = { ...base, ...classNamesOverride };
  const labels: ChartSeriesViewportLabels = { ...DEFAULT_LABELS, ...labelsOverride };
  const ghost = ghostButtonClassName ?? ghostBtnBemClasses(prefix);

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
    <div className={cn.root}>
      {navigable ? (
        <div className={cn.nav} role="toolbar" aria-label={labels.toolbarAria}>
          <div className={cn.actions}>
            <button
              type="button"
              className={`${ghost} ${cn.button}`}
              onClick={onStart}
              disabled={atStart}
              aria-label={labels.start}
              title={labels.start}
            >
              <ChevronsLeft size={16} aria-hidden="true" />
            </button>
            <button
              type="button"
              className={`${ghost} ${cn.button}`}
              onClick={onPrevPage}
              disabled={atStart}
              aria-label={labels.prev}
              title={labels.prev}
            >
              <ChevronLeft size={16} aria-hidden="true" />
            </button>
            <button
              type="button"
              className={`${ghost} ${cn.button}`}
              onClick={onNextPage}
              disabled={atEnd}
              aria-label={labels.next}
              title={labels.next}
            >
              <ChevronRight size={16} aria-hidden="true" />
            </button>
            <button
              type="button"
              className={`${ghost} ${cn.button}`}
              onClick={onEnd}
              disabled={atEnd}
              aria-label={labels.end}
              title={labels.end}
            >
              <ChevronsRight size={16} aria-hidden="true" />
            </button>
          </div>
          <p className={cn.meta}>
            <span className={cn.range}>{rangeLabel}</span>
            <span className={cn.pages}>{labels.pages(page, pageCount, total)}</span>
          </p>
        </div>
      ) : null}

      <div
        ref={viewportRef}
        className={navigable ? `${cn.canvas} ${cn.canvasScrollable}` : cn.canvas}
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
