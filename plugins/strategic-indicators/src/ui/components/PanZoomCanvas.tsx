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

function getFullscreenElement() {
  if (typeof document === "undefined") {
    return null;
  }

  return (
    document.fullscreenElement ??
    (document as Document & { webkitFullscreenElement?: Element | null })
      .webkitFullscreenElement ??
    null
  );
}

async function requestBrowserFullscreen() {
  const root = document.documentElement;

  if (root.requestFullscreen) {
    await root.requestFullscreen();
    return;
  }

  const webkitRequest = (
    root as HTMLElement & { webkitRequestFullscreen?: () => Promise<void> }
  ).webkitRequestFullscreen;

  if (webkitRequest) {
    await webkitRequest.call(root);
  }
}

async function exitBrowserFullscreen() {
  if (document.exitFullscreen) {
    await document.exitFullscreen();
    return;
  }

  const webkitExit = (
    document as Document & { webkitExitFullscreen?: () => Promise<void> }
  ).webkitExitFullscreen;

  if (webkitExit) {
    await webkitExit.call(document);
  }
}

type PanZoomCanvasProps = {
  children: ReactNode;
  fitToken?: string | number;
  toolbar?: ReactNode;
  floatingControls?: ReactNode | ((viewportNav: ReactNode) => ReactNode);
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
  const [isFullscreen, setIsFullscreen] = useState(
    () =>
      typeof document !== "undefined" &&
      getFullscreenElement() === document.documentElement,
  );
  const panZoom = usePanZoom({
    fitToken: `${fitToken ?? ""}-${isFullscreen ? "fullscreen" : "normal"}`,
    fitPadding: isFullscreen ? 32 : immersive ? 72 : 56,
  });

  const toggleFullscreen = useCallback(async () => {
    try {
      if (getFullscreenElement()) {
        await exitBrowserFullscreen();
        return;
      }

      await requestBrowserFullscreen();
    } catch {
      // fullscreen pode falhar por política do navegador
    }
  }, []);

  useEffect(() => {
    const handleFullscreenChange = () => {
      const active = getFullscreenElement() === document.documentElement;
      setIsFullscreen(active);

      if (active) {
        window.requestAnimationFrame(() => {
          panZoom.fitToView();
        });
      }
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    document.addEventListener("webkitfullscreenchange", handleFullscreenChange);

    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      document.removeEventListener(
        "webkitfullscreenchange",
        handleFullscreenChange,
      );
    };
  }, [panZoom.fitToView]);

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
          onClick={() => void toggleFullscreen()}
          title={isFullscreen ? "Sair da tela cheia (Esc)" : "Tela cheia"}
          aria-label={isFullscreen ? "Sair da tela cheia" : "Entrar em tela cheia"}
          aria-pressed={isFullscreen}
        >
          {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
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
      }${isFullscreen ? " si-pan-zoom-shell--fullscreen" : ""} ${className}`.trim()}
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
                {typeof floatingControls === "function"
                  ? floatingControls(nav)
                  : floatingControls}
              </div>
            ) : (
              <div className="si-pan-zoom__floating-nav">{nav}</div>
            )}
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
