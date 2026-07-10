import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import { useEffect, useRef, useState, type ReactNode } from "react";

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

  useEffect(() => {
    if (!open) return;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target as Node | null;
      if (!target) return;
      const inside =
        anchorRef.current?.contains(target) || panelRef.current?.contains(target);
      if (!inside) setOpen(false);
    };

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [open]);

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
        className="td-deck-settings-accordion__body td-deck-settings-accordion__body--portal"
        role="dialog"
        aria-label={ariaLabel}
      >
        {children}
      </AnchoredPanelPortal>
    </div>
  );
}
