import { AnchoredPanelPortal, RibbonGroupSurfaceProvider } from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";
import { DeckRibbonTile } from "./DeckRibbonTile";

type Props = {
  icon: LucideIcon;
  label: string;
  hint?: string;
  panelLabel: string;
  children: ReactNode | ((close: () => void) => ReactNode);
  /** Classe extra no painel (largura do formulário / portal de menu). */
  panelClassName?: string;
  /**
   * `form` (padrão): chrome do tile-popover.
   * `menu`: sem chrome — cascata/galeria traz o próprio fundo.
   */
  panelVariant?: "form" | "menu";
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
  panelVariant = "form",
}: Props) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const close = () => setOpen(false);

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
          density="compact"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className={[
            panelVariant === "form"
              ? "td-deck-ribbon-tile-popover delpi-ui-popover-surface"
              : null,
            panelClassName,
          ]
            .filter(Boolean)
            .join(" ")}
          role="dialog"
          aria-label={panelLabel}
          onDismiss={close}
        >
          {/*
           * Controles aninhados (cor, select) usam exclusive=false via
           * section-popover — evita fechar o tile ao abrir o segundo popover.
           */}
          <RibbonGroupSurfaceProvider value="section-popover">
            {typeof children === "function" ? children(close) : children}
          </RibbonGroupSurfaceProvider>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}
