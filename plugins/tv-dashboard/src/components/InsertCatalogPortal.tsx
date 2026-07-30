import type { ReactNode, RefObject } from "react";
import { AnchoredPanelPortal, useRibbonSectionPopoverSurface } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";

type Props = {
  open: boolean;
  anchorRef: RefObject<HTMLDivElement | null>;
  panelRef: RefObject<HTMLDivElement | null>;
  className: string;
  ariaLabel: string;
  onDismiss: () => void;
  children: ReactNode;
};

/** Catálogo Inserir / Alterar tipo: portal na faixa; inline no popover da seção colapsada. */
export function InsertCatalogPortal({
  open,
  anchorRef,
  panelRef,
  className,
  ariaLabel,
  onDismiss,
  children,
}: Props) {
  const inSectionPopover = useRibbonSectionPopoverSurface();
  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
      className={className}
      role="menu"
      aria-label={ariaLabel}
      exclusive={!inSectionPopover}
      onDismiss={onDismiss}
    >
      {children}
    </AnchoredPanelPortal>
  );
}
