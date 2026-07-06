import { createPortal } from "react-dom";
import { Maximize2, Minimize2 } from "lucide-react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useDiagramFullscreen } from "../../hooks/useDiagramFullscreen";
import { HelpTooltip } from "../HelpTooltip";
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
  const layout = isFullscreen ? "fill" : "default";

  const shell = (
    <DiagramLayoutProvider layout={layout}>
      <div
        className={[
          "dashboard-transformometro",
          "tm-diagram-workspace",
          isFullscreen ? "tm-diagram-workspace--fullscreen" : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {isFullscreen ? (
          <header className="tm-diagram-workspace__header">
            <div className="tm-diagram-workspace__header-text">
              <h2 className="tm-diagram-workspace__title">{title}</h2>
              {subtitle ? <p className="ds-hint tm-diagram-workspace__subtitle">{subtitle}</p> : null}
            </div>
            <button type="button" className="ds-ghost-btn" onClick={exit}>
              <Minimize2 size={16} aria-hidden />
              Sair da tela cheia
            </button>
          </header>
        ) : enabled ? (
          <div className="tm-diagram-workspace__expand-row">
            <HelpTooltip
              content={TM_HELP_TOOLTIPS.diagramEditor.fullscreen}
              ariaLabel="Ajuda: tela cheia"
              wrap
              placement="bottom"
            >
              <button type="button" className="ds-ghost-btn tm-diagram-workspace__expand-btn" onClick={enter}>
                <Maximize2 size={16} aria-hidden />
                Tela cheia
              </button>
            </HelpTooltip>
          </div>
        ) : null}

        <div className="tm-diagram-workspace__body">{children}</div>
      </div>
    </DiagramLayoutProvider>
  );

  if (isFullscreen) {
    return createPortal(shell, document.body);
  }

  return shell;
}
