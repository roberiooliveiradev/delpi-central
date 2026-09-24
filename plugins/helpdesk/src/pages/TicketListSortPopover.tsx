import { ArrowUpDown } from "lucide-react";
import { useClickOutside } from "@delpi/plugin-ui/index";
import { useEffect, useId, useRef, useState } from "react";

import { helpTooltips } from "../content/helpTooltips";
import type { TicketListSortLevel } from "../presentation/ticketListViewModel";
import { TicketListSortBuilder } from "./TicketListSortBuilder";

export function TicketListSortPopover({
  levels,
  onChange,
  onApply,
  onBeforeOpen,
  summaryLabel,
}: {
  levels: TicketListSortLevel[];
  onChange: (next: TicketListSortLevel[]) => void;
  onApply: () => void;
  onBeforeOpen?: () => void;
  summaryLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelId = useId();

  // SelectField abre painel no body — useClickOutside ignora overlays aninhados.
  useClickOutside([wrapperRef], open, () => setOpen(false));

  useEffect(() => {
    if (!open) return;
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open]);

  return (
    <div className="helpdesk-anchored-popover" ref={wrapperRef}>
      <button
        type="button"
        className="helpdesk-anchored-popover__trigger delpi-ui-table-toolbar-action"
        aria-label={summaryLabel ? `Ordenar: ${summaryLabel}` : "Ordenar"}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => {
          if (!open) onBeforeOpen?.();
          setOpen((current) => !current);
        }}
      >
        <ArrowUpDown size={16} aria-hidden />
        {summaryLabel ? summaryLabel.replace(/^Ordenado por\s+/i, "") : "Ordenar"}
      </button>
      {open ? (
        <div
          id={panelId}
          className="helpdesk-anchored-popover__panel"
          role="dialog"
          aria-label="Ordenação"
        >
          <div className="helpdesk-anchored-popover__header">
            <strong className="helpdesk-anchored-popover__title">Ordenar</strong>
            <p className="helpdesk-anchored-popover__hint">{helpTooltips.sortBuilder.panel}</p>
          </div>
          <div className="helpdesk-anchored-popover__body">
            <TicketListSortBuilder
              levels={levels}
              onChange={onChange}
              onApply={() => {
                onApply();
                setOpen(false);
              }}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}
