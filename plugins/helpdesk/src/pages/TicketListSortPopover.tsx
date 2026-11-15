import { ArrowUpDown } from "lucide-react";

import { helpTooltips } from "../content/helpTooltips";
import type { TicketListSortLevel } from "../presentation/ticketListViewModel";
import { HelpdeskListToolbarPopover } from "../ui/helpdeskUi";
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
  const triggerLabel = summaryLabel
    ? summaryLabel.replace(/^Ordenado por\s+/i, "")
    : "Ordenar";

  return (
    <HelpdeskListToolbarPopover
      label={triggerLabel}
      icon={<ArrowUpDown size={16} aria-hidden />}
      ariaLabel={summaryLabel ? `Ordenar: ${summaryLabel}` : "Ordenar"}
      panelAriaLabel="Ordenação"
      panelTitle="Ordenar"
      panelHint={helpTooltips.sortBuilder.panel}
    >
      {(close) => (
        <TicketListSortBuilder
          levels={levels}
          onChange={onChange}
          onApply={() => {
            onApply();
            close();
          }}
        />
      )}
    </HelpdeskListToolbarPopover>
  );
}
