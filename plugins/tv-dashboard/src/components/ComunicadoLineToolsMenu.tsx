import { useRef } from "react";
import { Minus, Spline, Waypoints, Pencil, ArrowRight, GitBranch } from "lucide-react";
import {
  AnchoredPanelPortal,
  HintAction,
  useRibbonSectionPopoverSurface,
} from "@delpi/plugin-ui/index";
import {
  COMUNICADO_LINE_TOOLS,
  type ComunicadoLineToolId,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";

type Props = {
  open: boolean;
  anchorRef: React.RefObject<HTMLDivElement | null>;
  onSelectTool: (toolId: ComunicadoLineToolId) => void;
  onDismiss: () => void;
};

const TOOL_ICONS: Record<ComunicadoLineToolId, typeof Minus> = {
  line: Minus,
  "line-arrow": ArrowRight,
  "elbow-connector": GitBranch,
  "curved-connector": Spline,
  curve: Spline,
  polyline: Waypoints,
  scribble: Pencil,
};

/**
 * Menu Inserir → Linha: linha, seta, conectores, curva, polilinha e rabisco.
 */
export function ComunicadoLineToolsMenu({
  open,
  anchorRef,
  onSelectTool,
  onDismiss,
}: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const inSectionPopover = useRibbonSectionPopoverSurface();

  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
      className="delpi-ui-popover-surface td-line-tools td-line-tools--portal"
      role="menu"
      aria-label="Ferramentas de linha"
      density="compact"
      exclusive={!inSectionPopover}
      onDismiss={onDismiss}
    >
      <ul className="td-line-tools__list">
        {COMUNICADO_LINE_TOOLS.map((tool) => {
          const Icon = TOOL_ICONS[tool.id];
          const hint = tool.ready
            ? tool.label
            : `${tool.label}: disponível em breve (desenho no palco)`;
          return (
            <li key={tool.id}>
              <HintAction hint={hint} ariaLabel={tool.label} placement="right">
                <button
                  type="button"
                  role="menuitem"
                  className="td-line-tools__item"
                  disabled={!tool.ready}
                  aria-disabled={!tool.ready}
                  onClick={() => {
                    if (!tool.ready) return;
                    onSelectTool(tool.id);
                  }}
                >
                  <Icon size={16} strokeWidth={1.75} aria-hidden="true" />
                  <span>{tool.label}</span>
                </button>
              </HintAction>
            </li>
          );
        })}
      </ul>
    </AnchoredPanelPortal>
  );
}
