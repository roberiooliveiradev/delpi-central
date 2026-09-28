import { ArrowUpDown } from "lucide-react";
import { AnchoredPanelPortal } from "@delpi/plugin-ui/index";
import { useRef, useState } from "react";

import { helpTooltips } from "../content/helpTooltips";
import type { TicketListSortLevel } from "../presentation/ticketListViewModel";
import { TicketListSortBuilder } from "./TicketListSortBuilder";

export function TicketListSortPopover({
  levels,
  onChange,
  onApply,
  summaryLabel,
}: {
  levels: TicketListSortLevel[];
  onChange: (next: TicketListSortLevel[]) => void;
  onApply: () => void;
  summaryLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  return (
    <div className="helpdesk-anchored-popover" ref={wrapperRef}>
      <button
        type="button"
        className="helpdesk-anchored-popover__trigger delpi-ui-table-toolbar-action"
        aria-label={summaryLabel ? `Ordenar: ${summaryLabel}` : "Ordenar"}
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <ArrowUpDown size={16} aria-hidden />
        {summaryLabel ? summaryLabel.replace(/^Ordenado por\s+/i, "") : "Ordenar"}
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={wrapperRef}
        panelRef={panelRef}
        className="helpdesk-anchored-popover__panel"
        variant="bare"
        role="dialog"
        aria-label="Ordenação"
        preferredPlacement="bottom"
        horizontalAlign="end"
        gap={6}
        portalScopeClassName="dashboard-helpdesk"
        onDismiss={() => setOpen(false)}
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
      </AnchoredPanelPortal>
    </div>
  );
}
