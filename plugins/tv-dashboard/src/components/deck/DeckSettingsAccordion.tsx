import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import { useRef, useState, type ReactNode } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";

type Props = {
  summary: string;
  ariaLabel: string;
  children: ReactNode;
};

/** Botão compacto + painel ancorado (templates, filtros) na faixa da aba Tela. */
export function DeckSettingsAccordion({ summary, ariaLabel, children }: Props) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  return (
    <div className="td-deck-settings-accordion" ref={anchorRef}>
      <button
        type="button"
        className="td-deck-settings-accordion__summary"
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((prev) => !prev)}
      >
        {summary}
      </button>
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
