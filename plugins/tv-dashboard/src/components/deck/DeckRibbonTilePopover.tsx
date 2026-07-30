import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";
import { DeckRibbonTile } from "./DeckRibbonTile";

type Props = {
  icon: LucideIcon;
  label: string;
  hint?: string;
  panelLabel: string;
  children: ReactNode;
  /** Classe extra no painel (largura do formulário). */
  panelClassName?: string;
};

/**
 * Tile da faixa + popover ancorado — mesmo molde da aba Inserir
 * (ícone acima, rótulo abaixo; formulário fora da band).
 */
export function DeckRibbonTilePopover({
  icon,
  label,
  hint,
  panelLabel,
  children,
  panelClassName,
}: Props) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  return (
    <div ref={anchorRef} className="td-composer__dropdown">
      <DeckRibbonTile
        icon={icon}
        label={label}
        hint={hint}
        active={open}
        onClick={() => setOpen((prev) => !prev)}
      />
      {open ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={anchorRef}
          panelRef={panelRef}
          variant="bare"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className={["td-deck-ribbon-tile-popover", panelClassName].filter(Boolean).join(" ")}
          role="dialog"
          aria-label={panelLabel}
          onDismiss={() => setOpen(false)}
        >
          {children}
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
