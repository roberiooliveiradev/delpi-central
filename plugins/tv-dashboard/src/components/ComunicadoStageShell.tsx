import {
  Grid3x3,
  Hand,
  Maximize2,
  Ruler,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { applyStagePanScrollDelta } from "../utils/stagePan";
import {
  buildAxisRulerTicks,
  clampStageZoom,
  STAGE_RULER_SIZE_PX,
  STAGE_RULER_UNITS,
  STAGE_ZOOM_MAX,
  STAGE_ZOOM_MIN,
} from "../utils/stageViewport";
import { useComunicadoEditor } from "./comunicadoEditorContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const V = TV_DASHBOARD_HELP_TOOLTIPS.view;

type StageMetrics = {
  wrapW: number;
  wrapH: number;
  canvasW: number;
  canvasH: number;
  originL: number;
  originT: number;
  scrollL: number;
  scrollT: number;
};

const EMPTY_METRICS: StageMetrics = {
  wrapW: 0,
  wrapH: 0,
  canvasW: 0,
  canvasH: 0,
  originL: 0,
  originT: 0,
  scrollL: 0,
  scrollT: 0,
};

function measureStageMetrics(
  wrap: HTMLDivElement | null,
  canvas: HTMLDivElement | null,
  _zoom: number,
): StageMetrics {
  if (!wrap || !canvas) return EMPTY_METRICS;

  const wrapRect = wrap.getBoundingClientRect();
  const canvasRect = canvas.getBoundingClientRect();

  return {
    wrapW: wrap.clientWidth,
    wrapH: wrap.clientHeight,
    canvasW: canvas.offsetWidth,
    canvasH: canvas.offsetHeight,
    originL: canvasRect.left - wrapRect.left + wrap.scrollLeft,
    originT: canvasRect.top - wrapRect.top + wrap.scrollTop,
    scrollL: wrap.scrollLeft,
    scrollT: wrap.scrollTop,
  };
}

function StageRulerHorizontal({ metrics, zoom }: { metrics: StageMetrics; zoom: number }) {
  const pxPerUnit = metrics.canvasW > 0 ? (metrics.canvasW * zoom) / STAGE_RULER_UNITS : 0;
  const ticks = useMemo(
    () =>
      buildAxisRulerTicks(metrics.wrapW, pxPerUnit, metrics.originL, metrics.scrollL, STAGE_RULER_UNITS),
    [metrics.canvasW, metrics.originL, metrics.scrollL, metrics.wrapW, pxPerUnit],
  );

  return (
    <div className="td-stage-shell__ruler td-stage-shell__ruler--h" aria-hidden="true">
      {ticks.map((tick) => (
        <span
          key={`h-${tick.pos}-${tick.label ?? tick.major}`}
          className={[
            "td-stage-shell__tick",
            tick.major ? "td-stage-shell__tick--major" : "",
            tick.label ? "td-stage-shell__tick--labeled" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          style={{ left: `${tick.pos}px` }}
        >
          {tick.label ? <span className="td-stage-shell__tick-label">{tick.label}</span> : null}
        </span>
      ))}
    </div>
  );
}

function StageRulerVertical({ metrics, zoom }: { metrics: StageMetrics; zoom: number }) {
  const pxPerUnit = metrics.canvasH > 0 ? (metrics.canvasH * zoom) / STAGE_RULER_UNITS : 0;
  const ticks = useMemo(
    () =>
      buildAxisRulerTicks(metrics.wrapH, pxPerUnit, metrics.originT, metrics.scrollT, STAGE_RULER_UNITS),
    [metrics.canvasH, metrics.originT, metrics.scrollT, metrics.wrapH, pxPerUnit],
  );

  return (
    <div className="td-stage-shell__ruler td-stage-shell__ruler--v" aria-hidden="true">
      {ticks.map((tick) => (
        <span
          key={`v-${tick.pos}-${tick.label ?? tick.major}`}
          className={[
            "td-stage-shell__tick",
            tick.major ? "td-stage-shell__tick--major" : "",
            tick.label ? "td-stage-shell__tick--labeled" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          style={{ top: `${tick.pos}px` }}
        >
          {tick.label ? <span className="td-stage-shell__tick-label">{tick.label}</span> : null}
        </span>
      ))}
    </div>
  );
}

function ComunicadoStageStatusBar() {
  const {
    stageZoom,
    setStageZoom,
    fitStageToView,
    showStageGrid,
    setShowStageGrid,
    showStageGuides,
    setShowStageGuides,
    stagePanMode,
    setStagePanMode,
  } = useComunicadoEditor();

  const zoomPercent = Math.round(stageZoom * 100);

  return (
    <div className="td-stage-statusbar" role="toolbar" aria-label="Zoom e exibição do palco">
      <div className="td-stage-statusbar__toggles">
        <button
          type="button"
          className={[
            "td-stage-statusbar__toggle",
            showStageGrid ? "td-stage-statusbar__toggle--active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          title={V.grid}
          aria-label="Grade"
          aria-pressed={showStageGrid}
          onClick={() => setShowStageGrid(!showStageGrid)}
        >
          <Grid3x3 size={14} aria-hidden="true" />
        </button>
        <button
          type="button"
          className={[
            "td-stage-statusbar__toggle",
            showStageGuides ? "td-stage-statusbar__toggle--active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          title={V.guides}
          aria-label="Guias"
          aria-pressed={showStageGuides}
          onClick={() => setShowStageGuides(!showStageGuides)}
        >
          <Ruler size={14} aria-hidden="true" />
        </button>
        <button
          type="button"
          className={[
            "td-stage-statusbar__toggle",
            stagePanMode ? "td-stage-statusbar__toggle--active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          title={V.pan}
          aria-label="Pan"
          aria-pressed={stagePanMode}
          onClick={() => setStagePanMode(!stagePanMode)}
        >
          <Hand size={14} aria-hidden="true" />
        </button>
      </div>

      <div className="td-stage-statusbar__zoom">
        <button
          type="button"
          className="td-stage-statusbar__btn"
          title={H.zoomOut}
          aria-label="Diminuir zoom"
          disabled={stageZoom <= STAGE_ZOOM_MIN}
          onClick={() => setStageZoom(clampStageZoom(stageZoom - 0.1))}
        >
          <ZoomOut size={14} aria-hidden="true" />
        </button>
        <input
          type="range"
          className="td-stage-statusbar__slider"
          min={STAGE_ZOOM_MIN * 100}
          max={STAGE_ZOOM_MAX * 100}
          step={5}
          value={zoomPercent}
          aria-label="Zoom do palco"
          onChange={(event) => setStageZoom(clampStageZoom(Number(event.target.value) / 100))}
        />
        <button
          type="button"
          className="td-stage-statusbar__btn"
          title={H.zoomIn}
          aria-label="Aumentar zoom"
          disabled={stageZoom >= STAGE_ZOOM_MAX}
          onClick={() => setStageZoom(clampStageZoom(stageZoom + 0.1))}
        >
          <ZoomIn size={14} aria-hidden="true" />
        </button>
        <span className="td-stage-statusbar__percent" aria-live="polite">
          {zoomPercent}%
        </span>
        <button
          type="button"
          className="td-stage-statusbar__btn td-stage-statusbar__btn--fit"
          title={H.zoomFit}
          aria-label="Ajustar à janela"
          onClick={() => fitStageToView()}
        >
          <Maximize2 size={14} aria-hidden="true" />
          <span>Ajustar</span>
        </button>
      </div>
    </div>
  );
}

type Props = {
  children: ReactNode;
};

export function ComunicadoStageShell({ children }: Props) {
  const {
    stageZoom,
    showStageRulers,
    canvasWrapRef,
    canvasRef,
    stagePanMode,
    setStagePanMode,
  } = useComunicadoEditor();
  const [metrics, setMetrics] = useState<StageMetrics>(EMPTY_METRICS);
  const panDragRef = useRef<{
    pointerId: number;
    lastX: number;
    lastY: number;
  } | null>(null);

  const refreshMetrics = useCallback(() => {
    setMetrics(measureStageMetrics(canvasWrapRef.current, canvasRef.current, stageZoom));
  }, [canvasRef, canvasWrapRef, stageZoom]);

  useEffect(() => {
    refreshMetrics();
    const wrap = canvasWrapRef.current;
    const canvas = canvasRef.current;
    if (!wrap || !canvas) return;

    const observer = new ResizeObserver(() => refreshMetrics());
    observer.observe(wrap);
    observer.observe(canvas);

    return () => observer.disconnect();
  }, [canvasRef, canvasWrapRef, refreshMetrics]);

  useEffect(() => {
    if (!stagePanMode) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setStagePanMode(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [setStagePanMode, stagePanMode]);

  const handleScroll = useCallback(() => {
    refreshMetrics();
  }, [refreshMetrics]);

  const handlePanPointerDown = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      if (!stagePanMode) return;
      if (event.button !== 0) return;
      const wrap = canvasWrapRef.current;
      if (!wrap) return;
      event.preventDefault();
      wrap.setPointerCapture(event.pointerId);
      panDragRef.current = {
        pointerId: event.pointerId,
        lastX: event.clientX,
        lastY: event.clientY,
      };
      wrap.classList.add("td-composer__canvas-wrap--panning");
    },
    [canvasWrapRef, stagePanMode],
  );

  const handlePanPointerMove = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      const drag = panDragRef.current;
      if (!drag || drag.pointerId !== event.pointerId) return;
      const wrap = canvasWrapRef.current;
      if (!wrap) return;
      const dx = event.clientX - drag.lastX;
      const dy = event.clientY - drag.lastY;
      drag.lastX = event.clientX;
      drag.lastY = event.clientY;
      const next = applyStagePanScrollDelta(wrap, dx, dy);
      wrap.scrollLeft = next.scrollLeft;
      wrap.scrollTop = next.scrollTop;
    },
    [canvasWrapRef],
  );

  const endPanDrag = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      const drag = panDragRef.current;
      if (!drag || drag.pointerId !== event.pointerId) return;
      panDragRef.current = null;
      const wrap = canvasWrapRef.current;
      if (!wrap) return;
      if (wrap.hasPointerCapture(event.pointerId)) {
        wrap.releasePointerCapture(event.pointerId);
      }
      wrap.classList.remove("td-composer__canvas-wrap--panning");
    },
    [canvasWrapRef],
  );

  const shellStyle = {
    "--td-ruler-size": `${STAGE_RULER_SIZE_PX}px`,
    "--td-composer-zoom": stageZoom,
  } as CSSProperties;

  return (
    <div className="td-composer td-composer--deck td-stage-shell" style={shellStyle}>
      <div
        className={[
          "td-stage-shell__workspace",
          showStageRulers ? "td-stage-shell__workspace--rulers" : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {showStageRulers ? (
          <>
            <div className="td-stage-shell__corner" aria-hidden="true" />
            <StageRulerHorizontal metrics={metrics} zoom={stageZoom} />
            <StageRulerVertical metrics={metrics} zoom={stageZoom} />
          </>
        ) : null}
        <div
          ref={canvasWrapRef}
          className={[
            "td-composer__canvas-wrap",
            "td-composer__canvas-wrap--full",
            "td-composer__canvas-wrap--zoom",
            stagePanMode ? "td-composer__canvas-wrap--pan" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          onScroll={handleScroll}
          onPointerDown={handlePanPointerDown}
          onPointerMove={handlePanPointerMove}
          onPointerUp={endPanDrag}
          onPointerCancel={endPanDrag}
        >
          {children}
        </div>
      </div>
      <ComunicadoStageStatusBar />
    </div>
  );
}
