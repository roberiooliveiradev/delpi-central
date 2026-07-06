import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import { Maximize2, Minimize2, X } from "lucide-react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useDiagramFullscreen } from "../../hooks/useDiagramFullscreen";
import { DiagramLayoutProvider } from "./DiagramLayoutContext";

type Props = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  enabled?: boolean;
};

export function DiagramFullscreenFrame({
  title,
  subtitle,
  children,
  enabled = true,
}: Props) {
  const { isFullscreen, enter, exit } = useDiagramFullscreen();
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const layout = isFullscreen ? "fill" : "default";

  useEffect(() => {
    if (!isFullscreen) return;
    panelRef.current?.focus();
  }, [isFullscreen]);

  const inlineWorkspace = (
    <DiagramLayoutProvider layout={layout}>
      <div className="tm-diagram-workspace">
        {enabled && !isFullscreen ? (
          <div className="tm-diagram-workspace__expand-row">
            <button
              type="button"
              className="ds-ghost-btn tm-diagram-workspace__expand-btn"
              onClick={enter}
              title={TM_HELP_TOOLTIPS.diagramEditor.fullscreen}
            >
              <Maximize2 size={16} aria-hidden />
              Tela cheia
            </button>
          </div>
        ) : null}

        {!isFullscreen ? <div className="tm-diagram-workspace__body">{children}</div> : null}
      </div>
    </DiagramLayoutProvider>
  );

  const modal =
    typeof document === "undefined"
      ? null
      : createPortal(
          <div className="dashboard-transformometro tm-diagram-modal" role="presentation">
            <button
              type="button"
              className="tm-diagram-modal__backdrop"
              aria-label="Fechar tela cheia"
              onClick={exit}
            />
            <div
              ref={panelRef}
              className="tm-diagram-modal__panel"
              role="dialog"
              aria-modal="true"
              aria-labelledby={titleId}
              tabIndex={-1}
            >
              <header className="tm-diagram-modal__header">
                <div className="tm-diagram-modal__header-text">
                  <h2 id={titleId} className="tm-diagram-modal__title">
                    {title}
                  </h2>
                  {subtitle ? <p className="ds-hint tm-diagram-modal__subtitle">{subtitle}</p> : null}
                </div>
                <button type="button" className="ds-ghost-btn tm-diagram-modal__close" onClick={exit}>
                  <Minimize2 size={16} aria-hidden />
                  Sair da tela cheia
                </button>
                <button type="button" className="ds-ghost-btn tm-diagram-modal__close-icon" onClick={exit}>
                  <X size={16} aria-hidden />
                  <span className="sr-only">Fechar</span>
                </button>
              </header>
              <div className="tm-diagram-modal__body">
                <DiagramLayoutProvider layout="fill">{children}</DiagramLayoutProvider>
              </div>
            </div>
          </div>,
          document.body
        );

  return (
    <>
      {inlineWorkspace}
      {isFullscreen ? modal : null}
    </>
  );
}
