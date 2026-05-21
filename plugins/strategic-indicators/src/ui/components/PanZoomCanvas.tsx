import { useCallback, useEffect, useState, type ReactNode } from "react";
import {
  Maximize2,
  Minimize2,
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
  floatingControls?: ReactNode;
  className?: string;
  allowFullscreen?: boolean;
  immersive?: boolean;
};

export function PanZoomCanvas({
  children,
  fitToken,
  toolbar,
  floatingControls,
  className = "",
  allowFullscreen = true,
  immersive = false,
}: PanZoomCanvasProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const panZoom = usePanZoom({
    fitToken: `${fitToken ?? ""}-${isExpanded ? "expanded" : "normal"}`,
    fitPadding: isExpanded ? 40 : immersive ? 72 : 56,
  });

  const toggleExpanded = useCallback(() => {
    setIsExpanded((current) => !current);
  }, []);

  useEffect(() => {
    if (!isExpanded) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsExpanded(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [isExpanded]);

  useEffect(() => {
    if (!isExpanded) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      panZoom.fitToView();
    });

    return () => window.cancelAnimationFrame(frame);
  }, [isExpanded]);

  const nav = (
    <div className="si-pan-zoom__nav" aria-label="Navegação do mapa">
      <button
        type="button"
        className="si-pan-zoom__nav-btn"
        onClick={panZoom.zoomOut}
        title="Diminuir zoom"
        aria-label="Diminuir zoom"
      >
        <Minus size={16} />
      </button>
      <span className="si-pan-zoom__zoom-label">{panZoom.zoomPercent}%</span>
      <button
        type="button"
        className="si-pan-zoom__nav-btn"
        onClick={panZoom.zoomIn}
        title="Aumentar zoom"
        aria-label="Aumentar zoom"
      >
        <Plus size={16} />
      </button>
      {allowFullscreen ? (
        <button
          type="button"
          className="si-pan-zoom__nav-btn"
          onClick={toggleExpanded}
          title={isExpanded ? "Sair da tela cheia" : "Expandir mapa"}
          aria-label={isExpanded ? "Sair da tela cheia" : "Expandir mapa"}
          aria-pressed={isExpanded}
        >
          {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
      ) : null}
      <button
        type="button"
        className="si-pan-zoom__nav-btn"
        onClick={panZoom.fitToView}
        title="Ajustar à tela"
        aria-label="Ajustar à tela"
      >
        <RotateCcw size={16} />
      </button>
      <button
        type="button"
        className="si-pan-zoom__nav-btn"
        onClick={panZoom.resetView}
        title="Zoom 100% e posição inicial"
        aria-label="Restaurar visualização"
      >
        <span className="si-pan-zoom__reset-label">100%</span>
      </button>
    </div>
  );

  return (
    <div
      className={`si-pan-zoom-shell${
        immersive ? " si-pan-zoom-shell--immersive" : ""
      }${isExpanded ? " si-pan-zoom-shell--expanded" : ""} ${className}`.trim()}
    >
      {!immersive && (toolbar || floatingControls) ? (
        <div className="si-pan-zoom-shell__bar">
          {toolbar ? (
            <div className="si-pan-zoom-shell__toolbar">{toolbar}</div>
          ) : null}
          {nav}
        </div>
      ) : null}

      <div
        ref={panZoom.viewportRef}
        className={`si-pan-zoom__viewport${
          panZoom.isDragging ? " si-pan-zoom__viewport--dragging" : ""
        }`}
        {...panZoom.viewportProps}
      >
        {immersive ? (
          <div className="si-pan-zoom__floating-bar" data-pan-zoom-lock="true">
            {floatingControls ? (
              <div className="si-pan-zoom__floating-controls">
                {floatingControls}
              </div>
            ) : null}
            <div className="si-pan-zoom__floating-nav">{nav}</div>
          </div>
        ) : null}

        <div className="si-pan-zoom__hint">
          <Move size={14} aria-hidden />
          <span>
            Arraste para navegar · Scroll ou pinça para zoom · Espaço + arraste
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
