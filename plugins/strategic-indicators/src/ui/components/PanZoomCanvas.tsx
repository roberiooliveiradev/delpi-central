import type { ReactNode } from "react";
import {
  Maximize2,
  Minus,
  Move,
  Plus,
  RotateCcw,
} from "lucide-react";
import { usePanZoom, type PanZoomTransform } from "../hooks/usePanZoom";
import "./PanZoomCanvas.css";

type PanZoomCanvasProps = {
  children: ReactNode;
  fitToken?: string | number;
  toolbar?: ReactNode;
  className?: string;
};

export function PanZoomCanvas({
  children,
  fitToken,
  toolbar,
  className = "",
}: PanZoomCanvasProps) {
  const panZoom = usePanZoom({ fitToken, fitPadding: 56 });

  return (
    <div className={`si-pan-zoom-shell ${className}`.trim()}>
      <div className="si-pan-zoom-shell__bar">
        {toolbar ? (
          <div className="si-pan-zoom-shell__toolbar">{toolbar}</div>
        ) : null}

        <div className="si-pan-zoom-shell__nav" aria-label="Navegação do mapa">
          <button
            type="button"
            className="si-pan-zoom-shell__nav-btn"
            onClick={panZoom.zoomOut}
            title="Diminuir zoom"
            aria-label="Diminuir zoom"
          >
            <Minus size={16} />
          </button>
          <span className="si-pan-zoom-shell__zoom-label">
            {panZoom.zoomPercent}%
          </span>
          <button
            type="button"
            className="si-pan-zoom-shell__nav-btn"
            onClick={panZoom.zoomIn}
            title="Aumentar zoom"
            aria-label="Aumentar zoom"
          >
            <Plus size={16} />
          </button>
          <button
            type="button"
            className="si-pan-zoom-shell__nav-btn"
            onClick={panZoom.fitToView}
            title="Ajustar à tela"
            aria-label="Ajustar à tela"
          >
            <Maximize2 size={16} />
          </button>
          <button
            type="button"
            className="si-pan-zoom-shell__nav-btn"
            onClick={panZoom.resetView}
            title="Zoom 100% e posição inicial"
            aria-label="Restaurar visualização"
          >
            <RotateCcw size={16} />
          </button>
        </div>
      </div>

      <div
        ref={panZoom.viewportRef}
        className={`si-pan-zoom__viewport${
          panZoom.isDragging ? " si-pan-zoom__viewport--dragging" : ""
        }`}
        {...panZoom.viewportProps}
      >
        <div className="si-pan-zoom__hint">
          <Move size={14} aria-hidden />
          <span>
            Arraste para navegar · Scroll ou pinça para zoom · Espaço + arraste
            · Botões à direita para ajustar
          </span>
        </div>

        <div
          ref={panZoom.contentRef}
          className="si-pan-zoom__surface"
          style={panZoom.surfaceStyle}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

export type { PanZoomTransform };
