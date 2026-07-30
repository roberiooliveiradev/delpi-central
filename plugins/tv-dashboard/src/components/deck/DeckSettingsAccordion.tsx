import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";
import { DeckRibbonTile } from "./DeckRibbonTile";

type Props = {
  summary: string;
  ariaLabel: string;
  icon: LucideIcon;
  children: ReactNode;
};

/**
 * Tile «Inserir» + painel ancorado (templates, filtros) na faixa da aba Tela.
 * Substitui o chip/pill antigo que quebrava o alinhamento da band.
 */
export function DeckSettingsAccordion({ summary, ariaLabel, icon, children }: Props) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  return (
    <div className="td-deck-settings-accordion" ref={anchorRef}>
      <DeckRibbonTile
        icon={icon}
        label={summary}
        active={open}
        onClick={() => setOpen((prev) => !prev)}
      />
      <AnchoredPanelPortal
        open={open}
        anchorRef={anchorRef}
        panelRef={panelRef}
        variant="bare"
        portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
        className="td-deck-settings-accordion__body td-deck-settings-accordion__body--portal"
        role="dialog"
        aria-label={ariaLabel}
        onDismiss={() => setOpen(false)}
      >
        {children}
      </AnchoredPanelPortal>
    </div>
  );
}
